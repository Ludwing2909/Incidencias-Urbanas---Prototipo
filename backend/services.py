import json
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from backend.db import Rule
from backend.settings import ROOT
from ml.text import normalize
from backend.priority import prioritize

CATEGORY_CONFIG = json.loads((ROOT / 'config/categories.json').read_text(encoding='utf-8'))
CATEGORIES = CATEGORY_CONFIG['categories']
KEYWORDS = json.loads((ROOT / 'config/keywords.json').read_text(encoding='utf-8'))

def hints(text):
    lower = normalize(text).lower()
    return {cat for cat, words in KEYWORDS.items() if any(re.search(r'\b' + re.escape(w) + r'\w*\b', lower) for w in words)}

def review_reasons(text):
    lower = text.lower()
    reasons = []
    if len(re.findall(r'\w+', text)) < 4:
        reasons.append('texto insuficiente')
    if len(hints(text)) > 1:
        reasons.append('varios temas')
    if any(s in lower for s in ('licencia de conducir', 'certificado', 'trámite', 'tramite', 'reclamo administrativo', 'solicito información', 'apelación', 'recurso administrativo')):
        reasons.append('fuera de alcance')
    if any(s in lower for s in ('please', 'broken street', 'water leak', 'the road', 'jani', 'maypi', 'imaynalla', 'waliki', 'jallalla')):
        reasons.append('idioma no soportado')
    # Heurística conservadora; no acredita detección de idioma/OOD.
    if not hints(text):
        reasons.append('fuera de alcance')
    return list(dict.fromkeys(reasons))

def urgency(text):
    lower = text.lower()
    terms = ('incendio', 'herido', 'agresión en curso', 'electrocut', 'riesgo de derrumbe', 'arma de fuego', 'atropell')
    matches = [term for term in terms if term in lower and not re.search(r'\b(?:no|sin)\s+(?:hay\s+)?' + re.escape(term), lower)]
    return bool(matches), ('Coincidencia de alerta: ' + ', '.join(matches) + '. Requiere verificación humana.') if matches else None

def resolve_rule(db, topic, location):
    rules = list(db.scalars(select(Rule).where(Rule.category == topic, Rule.active == True)))
    return select_rule(rules,topic,location)

def select_rule(rules,topic,location=None):
    today = datetime.now(ZoneInfo('America/Lima')).date().isoformat()
    applicable = [r for r in rules if r.category == topic and r.active and r.valid_from <= today <= r.valid_until and normalize(r.territory).lower() in ('juliaca urbana', normalize(location or '').lower())]
    # Ambigüedad entre competencias tampoco se decide automáticamente.
    if len(applicable) != 1:
        return None
    return applicable[0]

def classify(db, predictor, text, location=None):
    start = time.perf_counter()
    try:
        topic, score, score_type = predictor.predict(text)
    except Exception:
        topic, score, score_type = None, None, None
    rule = resolve_rule(db, topic, location) if topic else None
    result = classification_result(topic,score,score_type,predictor.manifest,text,rule)
    return result, round((time.perf_counter() - start) * 1000)

def classification_result(topic,score,score_type,meta,text,rule=None,priority=None):
    reasons = review_reasons(text)
    if topic is None:
        reasons.append('modelo no disponible')
    threshold = meta.get('threshold')
    if topic is not None:
        if threshold is None or not meta.get('threshold_validated_real', False):
            reasons.append('umbral no validado')
        elif score_type != 'probabilidad_calibrada':
            reasons.append('puntuación no probabilística o sin calibración')
        elif score is None:
            reasons.append('puntuación no disponible')
        elif score < threshold:
            reasons.append('baja puntuación')
    if topic and rule is None:
        reasons.append('regla inexistente')
    if topic in ('C7', 'C8') or (rule and (not rule.validated or rule.conditions != 'incidencia urbana')):
        reasons.append('competencia no validada')
    if meta.get('demonstration', False) and topic:
        reasons.append('modelo demostrativo sin validación real')
    priority = priority or prioritize(text)
    urgent = priority['nivel']=='alta'
    urgent_reason = priority['motivo'] if urgent else None
    reasons = list(dict.fromkeys(reasons))
    result = dict(tema=topic, puntuacion=score, tipo_puntuacion=score_type,
        requiere_revision=bool(reasons), motivos_revision=reasons, ruta_revision='R9' if reasons else None,
        destino_sugerido=rule.destination if rule else None, prioridad=priority['nivel'], evaluacion_prioridad=priority,
        alerta_posible_urgencia=urgent, motivo_urgencia=urgent_reason,
        estado='Pendiente de revisión' if reasons else 'Sugerencia disponible',
        version_modelo=meta.get('version'), version_umbral=meta.get('threshold_version'),
        version_reglas=f'{rule.id}:v{rule.version}' if rule else None,
        demostrativo=meta.get('demonstration', False), destino=destination_info(rule, topic))
    return result

def destination_info(rule, topic):
    confirmed = bool(rule and rule.validated and rule.conditions == 'incidencia urbana' and topic not in ('C7','C8'))
    return {'area': rule.destination if rule else None, 'confirmada': confirmed,
        'mensaje': 'Área sugerida sujeta a revisión humana' if confirmed else 'Área responsable pendiente de confirmación',
        'validada': bool(rule and rule.validated), 'vigente': bool(rule),
        'desde': rule.valid_from if rule else None, 'hasta': rule.valid_until if rule else None,
        'version': f'{rule.id}:v{rule.version}' if rule else None,
        'origen': 'Reglas administrativas independientes del PLN'}
