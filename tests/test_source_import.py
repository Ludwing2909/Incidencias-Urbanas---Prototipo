import csv
import json
from pathlib import Path
import pytest
from ml.source_import import analyze_valladolid,mapping_index,require_free_text,EXPECTED
from ml.data import validate

ROOT=Path(__file__).resolve().parents[1]

def fixture_source(path):
    columns=['peticion','canal_entrada','fecha_peticion','tipo','estado','tema','fecha_cierre','canal_respuesta','x','y','LON','LAT']
    rows=[['101','Teléfono 010','31/07/2009','Queja','Finalizada','Calles. Limpieza','01/08/2009','Telefono010','100','200','3','4'],['102','APP','30/12/2020','Queja','Finalizada','Tasa de basuras','31/12/2020','E-Mail','','','',''],['103','APP','30/12/2020','Queja','Finalizada','Jardines. Limpieza','31/12/2020','E-Mail','','','',''],['104','APP','30/12/2020','Queja','Finalizada','ALUMBRADO PÚBLICO','31/12/2020','E-Mail','','','',''],['105','APP','fecha inválida','','Analizada','','','E-Mail','','','','']]
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter=';');writer.writerow(columns);writer.writerows(rows)

def test_no_free_text_and_aggregate_reconciliation(tmp_path):
    source=tmp_path/'original.csv';fixture_source(source)
    before=source.read_bytes()
    output=tmp_path/'report.json';tables=tmp_path/'tables'
    report=analyze_valladolid(source,output,tables)
    assert source.read_bytes()==before
    assert report['rows']==5 and report['numeric_request_ids']==5
    assert not report['has_free_text'] and not report['training_eligible']
    assert report['training_rows_extracted']==0
    assert sum(report['by_mapping_status'].values())==5
    assert report['by_category']['C1']==1 and report['by_category']['C7']==1
    assert report['by_category']['C6']==0
    assert report['privacy']['coordinate_rows_excluded']==1
    assert report['period']['invalid_dates']==1
    assert report['period']['from']=='2009-07-31'
    assert report['by_mapping_status']['fuera_de_alcance']==1
    assert report['by_mapping_status']['ambiguo']==1
    # El resumen no expone filas/IDs/coordenadas.
    saved=json.loads(output.read_text(encoding='utf-8'))
    assert 'records' not in saved and 'request_ids' not in saved
    assert {p.name for p in tables.glob('*.csv')}=={'temas.csv','anios.csv','tipos.csv','correspondencias_c1_c8.csv'}
    with pytest.raises(ValueError,match='descripciones libres'):require_free_text(report)

def test_corpus_validator_rejects_administrative_file(tmp_path):
    path=tmp_path/'structured.csv';fixture_source(path)
    with pytest.raises(ValueError,match='registro estructurado sin descripciones libres'):validate(path)

def test_labels_cannot_be_renamed_as_real_citizen_texts(tmp_path):
    from ml.data import COLUMNS
    import pandas as pd
    path=tmp_path/'disguised.csv'
    rows=[['id-1','Calles. Limpieza','C1','valladolid_2020','real','true','g-1','train','','etiqueta renombrada','CC BY 3.0 ES'],['id-2','Alumbrado público','C7','valladolid_2020','real','true','g-2','train','','etiqueta renombrada','CC BY 3.0 ES']]
    pd.DataFrame(rows,columns=COLUMNS).to_csv(path,index=False)
    with pytest.raises(ValueError,match='Fuente registrada sin descripciones libres'):validate(path)

def test_changed_schema_requires_review(tmp_path):
    source=tmp_path/'changed.csv';source.write_text('peticion;tema\n1;Alumbrado público\n',encoding='utf-8')
    with pytest.raises(ValueError,match='Esquema distinto'):analyze_valladolid(source,tmp_path/'report.json',tmp_path/'tables')

def test_ambiguous_labels_not_forced_into_training_classes():
    config,index=mapping_index(ROOT/'config/valladolid_mapping.json')
    assert index['jardines. limpieza'][0] is None
    assert index['mobiliario urbano. tapas de registro'][0] is None
    assert index['tasa de basuras'][1]=='fuera_de_alcance'
    assert index['innovacion y comercio'][0] is None
    assert config['human_validated'] is False

def test_source_report_staff_only(client):
    assert client.get('/api/v1/admin/fuentes').status_code==401
    from tests.conftest import credentials
    credentials(client,'revisor')
    response=client.get('/api/v1/admin/fuentes')
    assert response.status_code==200
    reports=response.json()
    for report in reports:
        assert report['training_rows_extracted']==0 and report['has_free_text'] is False
        assert 'records' not in report
