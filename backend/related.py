"""Índice administrativo separado. Solo build_index ajusta TF-IDF, fuera de HTTP."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
from datetime import datetime, timezone
import joblib
from sqlalchemy import select
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.db import Incident
from ml.text import anonymize, normalize

MAX_INDEX_ROWS = 1000

def snapshot(db):
    rows = list(db.scalars(select(Incident).order_by(Incident.created_at,Incident.id).limit(MAX_INDEX_ROWS+1)))
    if len(rows)>MAX_INDEX_ROWS:
        raise ValueError('La referencia inicial permite hasta 1000 casos; amplíe el índice offline antes de usarla')
    data=[dict(id=r.id,text=r.text,location=r.location,created_at=r.created_at.isoformat()) for r in rows]
    fingerprint=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return rows,fingerprint

def build_index(db, directory):
    directory=Path(directory)
    rows,fingerprint=snapshot(db)
    if not rows:
        raise ValueError('No hay casos para indexar')
    vectorizer=TfidfVectorizer(preprocessor=anonymize,ngram_range=(1,2))
    matrix=vectorizer.fit_transform([r.text for r in rows])
    directory.mkdir(parents=True,exist_ok=True)
    version=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    artifact=directory/f'{version}.joblib'
    joblib.dump({'vectorizer':vectorizer,'matrix':matrix,'ids':[r.id for r in rows]},artifact)
    meta={'version':version,'artifact':artifact.name,'fingerprint':fingerprint,
        'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'n':len(rows),
        'sklearn':importlib.metadata.version('scikit-learn'),'created_at':datetime.now(timezone.utc).isoformat()}
    (directory/'active.tmp').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    (directory/'active.tmp').replace(directory/'active.json')
    return {k:v for k,v in meta.items() if k not in ('artifact','fingerprint')}

def search_related(db, row, directory, top_k=5, threshold=.25):
    try:
        rows,fingerprint=snapshot(db)
        directory=Path(directory)
        meta=json.loads((directory/'active.json').read_text(encoding='utf-8'))
        if meta['fingerprint']!=fingerprint:
            return {'estado':'no disponible','motivo':'Índice desactualizado; reconstruir fuera de HTTP','items':[]}
        artifact=(directory/meta['artifact']).resolve()
        if artifact.parent!=directory.resolve() or meta['sklearn']!=importlib.metadata.version('scikit-learn') or hashlib.sha256(artifact.read_bytes()).hexdigest()!=meta['sha256']:
            raise ValueError('Índice incompatible')
        index=joblib.load(artifact)  # Únicamente artefactos administrativos locales.
        scores=cosine_similarity(index['vectorizer'].transform([row.text]),index['matrix'])[0]
        candidates={r.id:r for r in rows}
        items=[]
        for id,score in zip(index['ids'],scores):
            other=candidates[id]
            if id==row.id or other.created_at>row.created_at or score<threshold or score<=0:
                continue
            items.append({'id':id,'codigo':other.code,'similitud_coseno':float(score),
                'ubicacion_general':other.location,'tema':other.current_topic,'fecha':other.created_at.isoformat(),
                'ubicacion_coincide':normalize(row.location).lower()==normalize(other.location).lower() if row.location and other.location else None,
                'diferencia_dias':(row.created_at-other.created_at).total_seconds()/86400})
        items.sort(key=lambda v:(-v['similitud_coseno'],v['id']))
        return {'estado':'disponible','version_indice':meta['version'],'items':items[:top_k],
            'umbral':threshold,'tipo_puntuacion':'similitud_coseno',
            'limite':'Similitud textual, no probabilidad ni identidad de incidencia. Lugar y tiempo son contexto de revisión. El índice se ajustó con casos hasta su fecha de construcción; no es evaluación histórica sin una reconstrucción con corte temporal.'}
    except (OSError,ValueError,KeyError,TypeError):
        return {'estado':'no disponible','motivo':'Índice ausente o incompatible; construir fuera de HTTP','items':[]}
