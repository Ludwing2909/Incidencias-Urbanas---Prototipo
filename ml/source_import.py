"""Inspección y extracción agregada de Valladolid, sin fabricar un corpus textual."""
import argparse
import csv
import hashlib
import json
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
from ml.data import sha
from ml.text import normalize

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'peticion','canal_entrada','fecha_peticion','tipo','estado','tema','fecha_cierre','canal_respuesta','x','y','LON','LAT'}

def key(value):
    return ''.join(c for c in unicodedata.normalize('NFD',normalize(value).casefold()) if not unicodedata.combining(c)).rstrip('.')

def mapping_index(path):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    index = {}
    for category, labels in config['compatible'].items():
        if category not in {f'C{i}' for i in range(1,9)}:
            raise ValueError('Categoría de correspondencia inválida')
        for label in labels:
            normalized = key(label)
            if normalized in index and index[normalized][0] != category:
                raise ValueError('Correspondencias contradictorias')
            index[normalized] = (category, 'compatible_orientativo', 'Etiqueta administrativa comparable; no acredita descripción, veracidad ni competencia local')
    for status, labels in [('ambiguo',config['ambiguous']),('fuera_de_alcance',config['out_of_scope'])]:
        for label in labels:
            normalized = key(label)
            if normalized in index:
                raise ValueError('Etiqueta repetida en estados diferentes')
            index[normalized] = (None,status,'La etiqueta sola no determina problema dominante' if status=='ambiguo' else 'Tema fuera del clasificador de incidencias urbanas')
    return config,index

def analyze_valladolid(source, report_path=ROOT/'reports/sources/valladolid_2020.json', tables_dir=ROOT/'reports/sources/valladolid_2020', mapping_path=ROOT/'config/valladolid_mapping.json'):
    source, report_path, tables_dir = Path(source),Path(report_path),Path(tables_dir)
    # C engine respeta comillas y saltos dentro de campos; nunca omitir filas malformadas.
    frame = pd.read_csv(source,sep=';',encoding='utf-8-sig',dtype=str,keep_default_na=False)
    if set(frame.columns) != EXPECTED:
        raise ValueError('Esquema distinto al inspeccionado; revisar columnas antes de extraer')
    if frame.empty:
        raise ValueError('Fuente vacía')
    config,index = mapping_index(mapping_path)
    dates = pd.to_datetime(frame.fecha_peticion,format='%d/%m/%Y',errors='coerce')
    topics=[]
    for label, count in frame.tema.value_counts(dropna=False).items():
        category,status,reason = index.get(key(label),(None,'sin_correspondencia','Etiqueta sin correspondencia documentada; requiere inspección'))
        if not normalize(label):
            category,status,reason = None,'vacio','No existe tema administrativo'
        topics.append({'tema_original':label,'registros':int(count),'categoria_orientativa':category,'estado_mapeo':status,'motivo':reason,'validado_humano':False})
    category_counts={f'C{i}':0 for i in range(1,9)}
    statuses={}
    for topic in topics:
        statuses[topic['estado_mapeo']] = statuses.get(topic['estado_mapeo'],0)+topic['registros']
        if topic['categoria_orientativa']:
            category_counts[topic['categoria_orientativa']] += topic['registros']
    type_counts={str(t):int(n) for t,n in frame.tipo.value_counts().items()}
    years=[{'anio':int(year),'registros':int(n)} for year,n in dates.dropna().dt.year.value_counts().sort_index().items()]
    coordinate_rows=int(frame[['x','y','LON','LAT']].ne('').any(axis=1).sum())
    result={
        'source_id':'valladolid_2020','entity':'Ayuntamiento de Valladolid','location':'Valladolid, España',
        'file_name':source.name,'access_date':datetime.now(ZoneInfo('America/Lima')).isoformat(),
        'source_url':'https://www.valladolid.es/es/temas/hacemos/open-data-datos-abiertos/catalogo-datos/ficheros-datos-elaborados-clasificados-sectores/sector-publico',
        'license':'CC BY 3.0 ES (condición general del portal, salvo indicación específica contraria)',
        'license_url':'https://www.valladolid.es/es/temas/hacemos/open-data-datos-abiertos',
        'attribution':'Fuente: Ayuntamiento de Valladolid, Incidencias, quejas, sugerencias y reclamaciones hasta 2020. Extracción y correspondencias orientativas del equipo del proyecto; sin respaldo institucional.',
        'sha256':sha(source),'bytes':source.stat().st_size,'encoding':'utf-8-sig','separator':';',
        'rows':len(frame),'columns':frame.columns.tolist(),'unique_request_ids':int(frame.peticion.nunique()),
        'numeric_request_ids':int(frame.peticion.str.fullmatch(r'\d+').sum()),
        'nonempty':{c:int(frame[c].str.strip().ne('').sum()) for c in frame.columns},
        'unique_topic_labels':int(frame.tema[frame.tema.ne('')].nunique()),
        'period':{'from':dates.min().date().isoformat() if dates.notna().any() else None,'to':dates.max().date().isoformat() if dates.notna().any() else None,'invalid_dates':int(dates.isna().sum())},
        'has_free_text':False,'training_eligible':False,'training_rows_extracted':0,
        'exclusion_reasons':['No contiene descripciones ciudadanas libres','peticion es un identificador; tema es la etiqueta administrativa','Usar tema como texto predictor filtraría la respuesta al modelo'],
        'privacy':{'coordinate_rows_excluded':coordinate_rows,'identifiers_exported':False,'coordinates_exported':False,'row_level_records_exported':False},
        'mapping_version':config['version'],'mapping_sha256':sha(mapping_path),'mapping_human_validated':False,
        'by_category':category_counts,'by_mapping_status':statuses,'by_type':type_counts,'by_year':years,'topics':topics,
        'limitations':['Solo análisis descriptivo de registros externos; no evaluación de Juliaca','Frecuencias no son prioridades, cuotas locales ni datos de entrenamiento','C6 no tiene correspondencia inequívoca en este mapeo','No se importaron registros como incidencias operativas ni se cambió el modelo']}
    report_path.parent.mkdir(parents=True,exist_ok=True)
    tables_dir.mkdir(parents=True,exist_ok=True)
    outputs={
        'temas.csv':pd.DataFrame(topics),
        'anios.csv':pd.DataFrame(years),
        'tipos.csv':pd.DataFrame([{'tipo':t,'registros':n} for t,n in type_counts.items()]),
        'correspondencias_c1_c8.csv':pd.DataFrame([{'categoria':c,'registros_orientativos':n,'uso':'analisis_descriptivo_no_entrenamiento'} for c,n in category_counts.items()])}
    for name,table in outputs.items():table.to_csv(tables_dir/name,index=False,encoding='utf-8')
    result['outputs']={name:{'sha256':sha(tables_dir/name),'rows':len(table)} for name,table in outputs.items()}
    report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

def require_free_text(report):
    if not report.get('has_free_text'):
        raise ValueError('Fuente excluida de entrenamiento: no hay descripciones libres. No utilizar peticion ni tema como texto_reclamo.')

def update_registry(report):
    config_path=ROOT/'config/sources.json'
    config=json.loads(config_path.read_text(encoding='utf-8'))
    for source in config:
        if source['id']==report['source_id']:
            source.update(license_catalog='https://creativecommons.org/licenses/by/3.0/es/',license_evidence=report['license_url'],language_catalog='español: etiquetas administrativas inspeccionadas',training_eligible=False,has_free_text=False,compatibility='Solo análisis descriptivo; no hay descripciones libres. No admite entrenamiento textual.',local_report='reports/sources/valladolid_2020.json')
    config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    inspections_path=ROOT/'reports/source_inspection.json'
    inspections=json.loads(inspections_path.read_text(encoding='utf-8')) if inspections_path.exists() else []
    previous=next((r for r in inspections if r['id']==report['source_id']),None)
    entry={**next(s for s in config if s['id']==report['source_id']),
        'access_date':report['access_date'],'rows':report['rows'],'columns':report['columns'],
        'training_approved':False,'sha256':report['sha256'],'encoding':report['encoding'],
        'status':'Copia local proporcionada por usuario e inspeccionada; excluida de entrenamiento por ausencia de texto libre',
        'previous_network_attempt':(previous.get('previous_network_attempt') or {k:previous.get(k) for k in ['access_date','status','error']}) if previous else None}
    inspections=[r for r in inspections if r['id']!=report['source_id']]+[entry]
    inspections_path.write_text(json.dumps(inspections,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description='Analizar Valladolid sin transformar etiquetas administrativas en textos ciudadanos')
    p.add_argument('source');p.add_argument('--report',default=str(ROOT/'reports/sources/valladolid_2020.json'));p.add_argument('--tables',default=str(ROOT/'reports/sources/valladolid_2020'));p.add_argument('--mapping',default=str(ROOT/'config/valladolid_mapping.json'))
    a=p.parse_args()
    try:
        result=analyze_valladolid(a.source,a.report,a.tables,a.mapping)
        if Path(a.report).resolve()==(ROOT/'reports/sources/valladolid_2020.json').resolve():
            update_registry(result)
        print(json.dumps({k:result[k] for k in ['source_id','rows','unique_topic_labels','has_free_text','training_rows_extracted','by_category','by_mapping_status','period']},ensure_ascii=False,indent=2))
    except ValueError as error:p.exit(2,str(error)+'\n')

if __name__=='__main__':main()
