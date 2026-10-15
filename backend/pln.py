"""Análisis educativo sin persistencia de casos ni entrenamiento."""
import re
from difflib import SequenceMatcher
from time import perf_counter
from backend.services import classification_result, resolve_rule, review_reasons, hints
from ml.text import anonymize, normalize
from ml.trace import TRACE_VERSION, model_description
from backend.priority import prioritize

PREPARATION_VERSION = 'normalize-anonymize-v1'
EXTRACTION_VERSION = 'extraction-rules-v1'


def extraction(text, location=None, answered=None):
    """Fragmentos literales; ningún valor se infiere de coordenadas ni clases."""
    fields = {}
    patterns = {'problema_principal': r'[^.!?]*(?:basura|residuos|bache|luminaria|alumbrado|fuga|desagüe|alcantarillado|robo|árbol|semaforo|semáforo)[^.!?]*',
        'lugar_general': r'\b(?:barrio|sector|urbanización|urbanizacion|parque)\s+[^,.;!?]{2,60}',
        'referencia_temporal': r'\b(?:desde\s+(?:ayer|hoy|hace\s+\d+\s+(?:días|dias|semanas))|ayer|hoy|anoche|esta mañana|hace\s+\d+\s+(?:días|dias|semanas))\b'}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        value = match.group().strip() if match else None
        fields[key] = {'valor': value, 'evidencia': value, 'origen': 'fragmento del mensaje' if value else None}
    if location:
        fields['lugar_general'] = {'valor': anonymize(location), 'evidencia': anonymize(location), 'origen': 'campo ubicación general'}
    questions = []
    answered = answered or {}
    for key, prompt in [('problema_principal','¿Qué problema principal deseas que se revise?'),('lugar_general','¿En qué barrio o sector ocurre, sin dirección exacta?'),('referencia_temporal','¿Desde cuándo ocurre o cuándo lo observaste?')]:
        if fields[key]['valor'] is None and key not in answered:
            questions.append({'id': key, 'pregunta': prompt})
    if len(hints(text)) > 1 and 'tema_principal' not in answered:
        questions.insert(0, {'id': 'tema_principal', 'pregunta': 'Se detectaron pistas de varios temas. ¿Cuál es el problema principal? Puedes continuar a revisión.'})
    return {'version': EXTRACTION_VERSION, 'campos': fields,
        'limite': 'Reglas de fragmentos, no comprensión semántica validada. Valores nulos y errores requieren corrección humana.'}, questions[:3]


def safe_diff(before, after):
    # No devolver los fragmentos sustituidos: podrían contener identidades.
    return [{'tipo': 'igual' if tag == 'equal' else 'cambio',
             'entrada': before[a:b] if tag == 'equal' else '[SEGMENTO OCULTO]',
             'salida': after[c:d]} for tag,a,b,c,d in SequenceMatcher(None,before,after).get_opcodes()]


def analyze(db, predictor, text, location=None, answered=None):
    total = perf_counter()
    meta = predictor.manifest
    stages = []
    def stage(id, name, started, output, status='aplicada', reason='Ejecución real', transforms=None, limitation=None, version=None, entry=None):
        stages.append(dict(id=id,nombre=name,estado=status,motivo=reason,entrada=entry or {},salida=output,
            transformaciones=transforms or [],version=version or meta.get('version'),
            tiempo_ms=round((perf_counter()-started)*1000,4),limitacion=limitation))
    start = perf_counter()
    normal = normalize(text)
    valid = bool(normal) and len(text) <= 3000
    stage('entrada','Entrada y validación',start,{'longitud':len(text),'longitud_normalizada':len(normal),'valida':valid,
        'idioma': 'Heurística de términos; no detector de idioma validado',
        'motivos':review_reasons(anonymize(normal)) if valid else ['Texto vacío o fuera de límites']},
        reason='Mismos límites y normalización que el registro',version=PREPARATION_VERSION)
    if not valid:
        return dict(version_traza=TRACE_VERSION,version_modelo=meta.get('version'),valida=False,etapas=stages,clasificacion=None,
            extraccion={},preguntas=[],tiempo_total_ms=round((perf_counter()-total)*1000,4))
    start = perf_counter()
    clean = anonymize(normal)
    safe_location = anonymize(location) if location else None
    stage('preparacion','Protección y preparación',start,{'texto':clean,'longitud':len(clean),
        'normalizacion_cambio':normal!=text,'redaccion_cambio':clean!=normal,'comparacion':safe_diff(normal,clean)},
        transforms=['Unicode NFC','Espacios normalizados','Redacción por expresiones regulares'],
        version=PREPARATION_VERSION,limitation='Redacción preliminar: no garantiza eliminar nombres o domicilios. La comparación oculta los segmentos detectados; use ejemplos sin datos personales.')
    start = perf_counter()
    description = model_description(predictor.model)
    records = []
    try:
        prediction, records = predictor.execute(clean, traced=True)
        topic,score,kind = prediction
        failure = topic is None
    except Exception:
        topic,score,kind = None,None,None
        failure = True
    model_ms = (perf_counter()-start)*1000
    for id,name in [('analizador','Análisis del texto'),('tfidf','Representación TF-IDF')]:
        start = perf_counter()
        if id == 'analizador':
            output = {'miembros':[{k:r[k] for k in ('miembro','caracteristicas','caracteristicas_total','caracteristicas_unicas','caracteristicas_truncadas','vocabulario_tamano','parametros')} for r in records]}
        else:
            output = {'miembros':[{k:r[k] for k in ('miembro','pesos','pesos_truncados','no_nulas','vector_vacio','tiempo_ms')} for r in records],
                'definicion': 'Frecuencia: conteo del analizador. IDF: idf_ ajustado en entrenamiento. Peso: valor final transform, después de binary/sublinear_tf y normalización configurados. Cada miembro calibrado tiene su propio vocabulario.',
                'vector_vacio': bool(records) and all(r['vector_vacio'] for r in records)}
        stage(id,name,start,output,status='aplicada' if records else 'no disponible',reason='Observación del transform utilizado en la predicción' if records else 'Modelo ausente o sin vectorizador observable',
            limitation='Las características se acotan a 80 y los pesos a 30 por miembro. Los pesos no explican causalidad de la decisión.')
        stages[-1]['tiempo_ms'] = round(sum(r['tiempo_ms' if id=='tfidf' else 'analizador_ms'] for r in records),4)
    start = perf_counter()
    stage('clasificacion','Clasificación',start,{'tema':topic,'puntuacion':score,'tipo_puntuacion':kind,**description,
        'tiempo_inferencia_ms':round(model_ms,4)},status='no disponible' if failure else 'aplicada',reason='No se inventa una salida cuando falla el modelo' if failure else 'Salida del artefacto cargado')
    stages[-1]['tiempo_ms'] = round(model_ms,4)
    start = perf_counter()
    rule = resolve_rule(db,topic,safe_location) if topic else None
    rule_ms = (perf_counter()-start)*1000
    start = perf_counter()
    priority_started=perf_counter()
    priority=prioritize(clean)
    priority_ms=(perf_counter()-priority_started)*1000
    result = classification_result(topic,score,kind,meta,clean,rule,priority)
    stage('revision','Revisión humana',start,{'requiere_revision':result['requiere_revision'],'ruta':result['ruta_revision'],
        'motivos':result['motivos_revision'],'umbral':meta.get('threshold'),'umbral_validado':meta.get('threshold_validated_real',False)},
        limitation='Una puntuación alta no elimina el bloqueo por umbral, demostración o competencia.',version='review-policy-v2')
    start=perf_counter()
    stage('prioridad','Prioridad del mensaje',start,result['evaluacion_prioridad'],version=result['evaluacion_prioridad']['version'],
        limitation='Reglas orientativas basadas en riesgo e impacto descritos, independientes del clasificador temático; requiere revisión humana.')
    stages[-1]['tiempo_ms']=round(priority_ms,4)
    start = perf_counter()
    stage('destino','Destino administrativo',start,result['destino'],reason='Consulta de reglas, independiente del clasificador',version=result['version_reglas'] or 'administrative-policy-v1')
    stages[-1]['tiempo_ms']=round(rule_ms,4)
    start = perf_counter()
    extracted, questions = extraction(clean,safe_location,answered)
    stage('extraccion','Extracción orientativa',start,extracted,version=EXTRACTION_VERSION,limitation=extracted['limite'])
    for id,name in [('stopwords','Eliminación de stopwords'),('lematizacion','Lematización'),('stemming','Stemming'),('entidades','Reconocimiento de entidades'),('resumen','Resumen automático'),('multilabel','Clasificación multilabel')]:
        start=perf_counter()
        configured_stopwords = id=='stopwords' and records and any(r['parametros']['stop_words'] for r in records)
        stage(id,name,start,{},status='aplicada' if configured_stopwords else 'omitida' if id=='stopwords' and records else 'no implementada',reason='Configuración del vectorizador' if configured_stopwords else 'No se ejecuta en esta configuración' if id=='stopwords' and records else 'No se ejecuta; propuesta pendiente',version=TRACE_VERSION)
    start=perf_counter()
    stage('resultado','Resultado y siguiente paso',start,{'tema':topic,'revision':result['estado'],
        'siguiente_paso':'Continuar a revisión humana o registrar explícitamente en el formulario ciudadano',
        'registro_creado':False,'preguntas':questions})
    return dict(version_traza=TRACE_VERSION,version_modelo=meta.get('version'),valida=True,etapas=stages,clasificacion=result,
        extraccion=extracted,preguntas=questions,tiempo_total_ms=round((perf_counter()-total)*1000,4))
