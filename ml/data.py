import hashlib
import csv
import json
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import StratifiedGroupKFold
from ml.inference import LABELS
from ml.text import normalize, anonymize

COLUMNS = ['id','texto_reclamo','categoria','fuente','tipo_dato','validado','grupo_origen','particion','motivo_revision','transformacion','licencia_autorizacion']
PARTITIONS = {'','train','validation','test','challenge','functional'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def near_pairs(frame, threshold=.92):
    texts = frame.texto_reclamo.map(lambda t: normalize(t).lower()).tolist()
    pairs = []
    for i, first in enumerate(texts):
        for j in range(i):
            if SequenceMatcher(None,first,texts[j]).ratio() >= threshold:
                pairs.append((j,i))
    return pairs

def validate(path, check_partitions=True):
    with Path(path).open(encoding='utf-8-sig') as source:
        first_line=source.readline()
    if ';' in first_line:
        header=set(next(csv.reader([first_line],delimiter=';')))
        if {'peticion','tema'}.issubset(header) and 'texto_reclamo' not in header:
            raise ValueError('Valladolid es un registro estructurado sin descripciones libres: peticion es un ID y tema una etiqueta. No sirve como corpus textual de entrenamiento.')
    frame = pd.read_csv(path,encoding='utf-8-sig',dtype=str,keep_default_na=False)
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        if {'peticion','tema'}.issubset(frame.columns) and 'texto_reclamo' not in frame.columns:
            raise ValueError('Valladolid es un registro estructurado sin descripciones libres: peticion es un ID y tema una etiqueta. No sirve como corpus textual de entrenamiento.')
        raise ValueError('Faltan columnas: ' + ', '.join(sorted(missing)))
    if frame.empty:
        raise ValueError('Dataset vacío; complete la plantilla antes de entrenar')
    for col in ['id','texto_reclamo','fuente','tipo_dato','validado','grupo_origen','licencia_autorizacion']:
        if frame[col].str.strip().eq('').any():
            raise ValueError(f'Valores vacíos en {col}')
    if frame.id.duplicated().any():
        raise ValueError('IDs duplicados')
    if not frame.categoria.isin(LABELS + ['']).all():
        raise ValueError('Solo se admiten C1–C8 o tema nulo; R9 no es clase')
    if not frame.tipo_dato.isin(['real','elaborado']).all() or not frame.validado.isin(['true','false']).all():
        raise ValueError('tipo_dato/validado inválidos')
    registry=Path(__file__).resolve().parents[1]/'config/sources.json'
    sources=json.loads(registry.read_text(encoding='utf-8'))
    blocked={s['id'] for s in sources if s.get('has_free_text') is False}
    if (frame.tipo_dato.eq('real') & frame.fuente.isin(blocked)).any():
        raise ValueError('Fuente registrada sin descripciones libres: no convertir etiquetas administrativas en texto real de entrenamiento o evaluación.')
    if not frame.particion.isin(PARTITIONS).all():
        raise ValueError('Partición inválida')
    if (frame.categoria.eq('') & ~frame.particion.isin(['challenge','functional'])).any():
        raise ValueError('Tema nulo solo en desafíos o pruebas funcionales')
    if (frame.particion.isin(['train','validation','test']) & frame.validado.ne('true')).any():
        raise ValueError('Anotaciones no validadas no ingresan al experimento')
    if (frame.tipo_dato.eq('elaborado') & frame.particion.isin(['validation','test'])).any():
        raise ValueError('Ejemplos elaborados no sustituyen validación/prueba reales')
    normalized = frame.texto_reclamo.map(lambda s: normalize(s).lower())
    if normalized.duplicated().any():
        raise ValueError('Textos duplicados exactos; resolver antes de experimentar')
    for group, block in frame.groupby('grupo_origen'):
        if block.tipo_dato.nunique() > 1:
            raise ValueError('Un grupo no puede mezclar procedencia real y elaborada')
        if check_partitions and block.particion.nunique() > 1:
            raise ValueError(f'Fuga de grupo: {group}')
    pairs = near_pairs(frame)
    for i,j in pairs:
        if frame.iloc[i].grupo_origen != frame.iloc[j].grupo_origen:
            raise ValueError(f'Duplicados cercanos con grupos distintos: {frame.iloc[i].id}, {frame.iloc[j].id}')
        if check_partitions and frame.iloc[i].particion != frame.iloc[j].particion:
            raise ValueError('Duplicados cercanos cruzan particiones')
    return frame

def folds(frame, max_folds=5, seed=42):
    if set(frame.categoria) != set(LABELS):
        raise ValueError('Entrenamiento requiere soporte de las ocho clases')
    counts = frame.groupby('categoria').grupo_origen.nunique()
    n = min(max_folds, int(counts.min()))
    if n < 2:
        raise ValueError('Validación cruzada no viable: se requieren al menos dos grupos por clase')
    # Reducir pliegues si la combinación de grupos no preserva soporte.
    for count in range(n,1,-1):
        cv = list(StratifiedGroupKFold(count,shuffle=True,random_state=seed).split(frame.texto_reclamo,frame.categoria,frame.grupo_origen))
        if all(set(frame.iloc[a].categoria) == set(LABELS) and set(frame.iloc[b].categoria) == set(LABELS) for a,b in cv):
            return cv
    raise ValueError('No hay pliegues estratificados viables con soporte de C1–C8; recupere más grupos independientes')

def split_data(source, output, seed=42):
    frame = validate(source,check_partitions=False)
    # Prueba reservada se conserva antes de cualquier selección.
    reserved_groups = set(frame.loc[frame.particion.eq('test'),'grupo_origen'])
    if any(len(set(g.particion)) > 1 for _,g in frame[frame.grupo_origen.isin(reserved_groups)].groupby('grupo_origen')):
        raise ValueError('La prueba reservada comparte grupos con desarrollo')
    eligible = frame.tipo_dato.eq('real') & frame.categoria.ne('') & ~frame.particion.isin(['test','challenge','functional'])
    real = frame[eligible].reset_index()
    if not real.empty:
        if set(real.categoria) != set(LABELS) or real.groupby('categoria').grupo_origen.nunique().min() < 5:
            raise ValueError('60/20/20 requiere al menos cinco grupos reales por clase; reserve test externo o documente adaptación')
        cv = list(StratifiedGroupKFold(5,shuffle=True,random_state=seed).split(real.texto_reclamo,real.categoria,real.grupo_origen))
        test_groups = set(real.iloc[cv[0][1]].grupo_origen) if not reserved_groups else set()
        validation_groups = set(real.iloc[cv[1][1]].grupo_origen)
        for _, row in real.iterrows():
            frame.loc[row['index'],'particion'] = 'test' if row.grupo_origen in test_groups else 'validation' if row.grupo_origen in validation_groups else 'train'
    frame.loc[frame.tipo_dato.eq('elaborado') & ~frame.particion.isin(['challenge','functional']),'particion'] = 'train'
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(output,index=False,encoding='utf-8')
    validate(output)
    manifest = {'seed':seed,'input_sha256':sha(source),'output_sha256':sha(output),'partitions':{p:frame.loc[frame.particion.eq(p),'id'].tolist() for p in sorted(set(frame.particion))},'groups':{p:sorted(set(frame.loc[frame.particion.eq(p),'grupo_origen'])) for p in sorted(set(frame.particion))},'counts':frame.groupby(['tipo_dato','particion','categoria']).size().to_dict()}
    manifest['counts'] = {'|'.join(k):int(v) for k,v in manifest['counts'].items()}
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    return manifest

def prepare(source, output):
    # No modifica originales. Aprobación humana de identidades residuales sigue siendo necesaria.
    frame = pd.read_csv(source,dtype=str,keep_default_na=False,encoding='utf-8-sig')
    frame = frame.loc[frame.texto_reclamo.str.strip().ne('')].copy()
    frame.texto_reclamo = frame.texto_reclamo.map(anonymize)
    frame.transformacion = frame.transformacion.map(lambda s:(s+'; redaccion-regex-v1; revision-humana-pendiente').strip('; '))
    frame.validado = 'false'
    frame.to_csv(output,index=False,encoding='utf-8')
    manifest = {'original_hash':sha(source),'output_hash':sha(output),'rows':len(frame),'human_review_required':True}
    Path(output).with_suffix('.privacy.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

def agreement(path):
    frame = pd.read_csv(path,dtype=str,keep_default_na=False)
    required = ['id','anotador_a','anotador_b']
    if not set(required).issubset(frame.columns) or frame.empty or frame.id.duplicated().any():
        raise ValueError('Contrato: id único, anotador_a, anotador_b; al menos una fila')
    allowed = LABELS + ['SIN_TEMA']
    if not frame.anotador_a.isin(allowed).all() or not frame.anotador_b.isin(allowed).all():
        raise ValueError('Anotaciones deben ser C1–C8 o SIN_TEMA')
    kappa = cohen_kappa_score(frame.anotador_a,frame.anotador_b)
    return {'n':len(frame),'agreement':float((frame.anotador_a == frame.anotador_b).mean()),'cohen_kappa':float(kappa) if np.isfinite(kappa) else None,'before_adjudication':True}
