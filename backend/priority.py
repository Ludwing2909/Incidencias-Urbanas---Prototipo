"""Priorización orientativa por evidencia explícita; independiente del tema PLN."""
import re
import unicodedata

VERSION='priority-rules-v1'
RULES=[
    ('alta','riesgo para personas',r'\b(?:incendio|herid\w*|agresion en curso|arma de fuego|riesgo de derrumbe|electrocut\w*|cables? (?:expuestos?|caidos?)|atropell\w*)\b',True),
    ('alta','servicio o acceso esencial interrumpido',r'\b(?:aguas residuales (?:entran|ingresan)|desague (?:entra|ingresa) a las casas|via completamente bloqueada|sin agua potable en todo el barrio)\b',True),
    ('media','fallo de servicio o infraestructura',r'\b(?:baches?|fuga de agua|basura acumulada|residuos acumulados|desague obstruido|semaforo (?:apagado|averiado)|luminaria\w*[^.!?;]{0,45}(?:apagada|no enciende)|alumbrado[^.!?;]{0,45}(?:apagado|no funciona)|no (?:hay|tenemos) (?:agua|alumbrado))\b',True),
    ('media','problema persistente',r'\b(?:desde hace \d+ dias|lleva\w* varios dias|desde ayer|varios dias|impide\w* el paso)\b',False),
    ('baja','mantenimiento o mejora sin riesgo descrito',r'\b(?:poda|ornato|pintura|pintar|mantenimiento preventivo|sugerencia|mejorar la apariencia|banca\w*|banco\w*)\b',False),
]

def prioritize(text):
    normalized=''.join(c for c in unicodedata.normalize('NFD',text.lower()) if unicodedata.category(c)!='Mn')
    evidence=[]
    for level,reason,pattern,negatable in RULES:
        for match in re.finditer(pattern,normalized):
            prefix=re.split(r'[.!?;,]|\b(?:pero|aunque)\b',normalized[:match.start()])[-1]
            if negatable and re.search(r'\b(?:no|sin|niega|descartado)\b(?:\W+\w+){0,5}\W*$',prefix):
                continue
            # Los offsets no cambian al quitar tildes españolas: la evidencia conserva el original.
            evidence.append({'nivel':level,'criterio':reason,'fragmento':text[match.start():match.end()]})
    for level in ('alta','media','baja'):
        selected=[e for e in evidence if e['nivel']==level]
        if selected:
            return {'nivel':level,'motivo':'; '.join(dict.fromkeys(e['criterio'] for e in selected)),
                'evidencias':selected[:8],'version':VERSION,'requiere_revision':True}
    return {'nivel':'media','motivo':'Información insuficiente para determinar riesgo o impacto; revisar prioridad',
        'evidencias':[],'version':VERSION,'requiere_revision':True}
