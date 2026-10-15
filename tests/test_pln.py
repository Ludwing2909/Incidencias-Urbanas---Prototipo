import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
import pytest
from sqlalchemy import select,func
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.db import SessionLocal,Incident,Prediction,StateHistory,Audit,AnalysisVersion,RelationDecision
from backend.main import app
from backend.pln import analyze,extraction
from backend.pln_metadata import experimental_audit,public_metadata
from backend.related import build_index,search_related
from ml.inference import Predictor
from ml.text import anonymize
from tests.conftest import credentials
from tests.test_api import register

@pytest.fixture(scope='module')
def real_predictor():
    p=Predictor(Path(__file__).parents[1]/'models/active.json')
    assert p.model is not None,'Reproduzca el artefacto demo antes de ejecutar estas pruebas de integración con el modelo'
    return p

@pytest.mark.parametrize('message',['Hay basura acumulada en el parque desde ayer.','No hay incendio, solo una luminaria apagada.','Basura y baches en el barrio.','xyzzy qqqq zzzzzz','La luminaria no enciende.'])
def test_real_trace_matches_prediction_without_fit(real_predictor,message):
    p=real_predictor
    before=[m.estimator.steps[:] for m in p.model.calibrated_classifiers_]
    expected=p.predict(message)
    with patch.object(TfidfVectorizer,'fit',side_effect=AssertionError('No fit')),patch.object(TfidfVectorizer,'fit_transform',side_effect=AssertionError('No fit_transform')):
        traced,records=p.execute(message,True)
    assert traced==expected and len(records)==len(p.model.calibrated_classifiers_)
    for original,current in zip(before,p.model.calibrated_classifiers_):
        assert current.estimator.steps==original
    for record,member in zip(records,p.model.calibrated_classifiers_):
        v=member.estimator.named_steps['tfidf']
        vector=v.transform([anonymize(message)])
        names=v.get_feature_names_out()
        weights={str(names[i]):float(w) for i,w in zip(vector.indices,vector.data)}
        assert record['no_nulas']==vector.nnz
        for feature in record['pesos']:
            assert feature['peso']==weights[feature['termino']]
            assert feature['idf']==v.idf_[v.vocabulary_[feature['termino']]]
    if message=='xyzzy qqqq zzzzzz':
        assert all(r['vector_vacio'] for r in records)

def test_trace_concurrency_keeps_shared_artifact(real_predictor):
    p=real_predictor
    samples=['Hay basura junto a la vía pública.','La luminaria no enciende.']*4
    expected=[p.predict(s) for s in samples]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda s:p.execute(s,True)[0],samples))
    assert results==expected

def test_public_analysis_no_case_writes_same_as_registration(client,real_predictor):
    app.state.predictor=real_predictor
    message='Hay basura acumulada en la vía pública desde ayer.'
    with patch.object(TfidfVectorizer,'fit',side_effect=AssertionError('No fit')):
        r=client.post('/api/v1/pln/analizar',json={'descripcion':message})
    assert r.status_code==200
    result=r.json()
    with SessionLocal() as db:
        for model in (Incident,Prediction,StateHistory,Audit,AnalysisVersion,RelationDecision):
            assert db.scalar(select(func.count()).select_from(model))==0
    registered=register(client,message).json()
    assert registered['clasificacion']==result['clasificacion']
    assert 'codigo' not in result and 'secreto_seguimiento' not in json.dumps(result)
    assert result['clasificacion']['requiere_revision']
    assert 'umbral no validado' in result['clasificacion']['motivos_revision']
    public=client.get('/api/v1/pln/metadatos').json()
    assert public['modelo']['estimador']=='LinearSVC'
    assert public['modelo']['metodo_base']=='decision_function'
    assert public['modelo']['metodo_salida']=='predict_proba'
    assert 'train_ids' not in json.dumps(public)

def test_privacy_and_missing_stages(client):
    response=client.post('/api/v1/pln/analizar',json={'descripcion':'Hay basura, DNI 12345678, teléfono 987654321, correo alguien@example.org.'})
    assert response.status_code==200
    data=response.json();serialized=json.dumps(data)
    for raw in ('12345678','987654321','alguien@example.org'):
        assert raw not in serialized
    states={s['id']:s['estado'] for s in data['etapas']}
    assert states['tfidf']=='no disponible'
    assert states['lematizacion']=='no implementada'
    assert data['clasificacion']['tema'] is None
    assert client.post('/api/v1/pln/analizar',json={'descripcion':'   '}).json()['valida'] is False
    assert client.post('/api/v1/pln/analizar',json={'descripcion':''}).status_code==422
    assert client.post('/api/v1/pln/analizar',json={'descripcion':'x'*3001}).status_code==422

def test_inference_failure_remains_explicit_without_breaking_register(client,real_predictor,monkeypatch):
    app.state.predictor=real_predictor
    def broken(_):raise RuntimeError('Fallo simulado del estimador')
    monkeypatch.setattr(real_predictor.model,'predict_proba',broken)
    data=client.post('/api/v1/pln/analizar',json={'descripcion':'Hay basura acumulada en la vía pública.'}).json()
    assert data['clasificacion']['tema'] is None and data['clasificacion']['puntuacion'] is None
    assert next(s for s in data['etapas'] if s['id']=='clasificacion')['estado']=='no disponible'
    saved=register(client)
    assert saved.status_code==201 and saved.json()['clasificacion']['tema'] is None
    assert 'Fallo simulado' not in json.dumps(data)

def test_high_score_unvalidated_threshold_is_not_called_low():
    from backend.services import classification_result
    data=classification_result('C1',.999,'probabilidad_calibrada',{'threshold':None},'Hay basura acumulada en la vía pública.')
    assert data['requiere_revision'] and 'umbral no validado' in data['motivos_revision']
    assert 'baja puntuación' not in data['motivos_revision']

def test_extraction_literal_and_no_repeat():
    e,q=extraction('Hay basura en el barrio Central desde ayer.')
    for field in e['campos'].values():
        assert field['evidencia'] in 'Hay basura en el barrio Central desde ayer.'
    assert not q
    e,q=extraction('Descripción sin referencia suficiente.',answered={'problema_principal':'respuesta','lugar_general':'respuesta','referencia_temporal':'respuesta'})
    assert not q and all(f['valor'] is None for f in e['campos'].values())

def test_authorized_clarifications_keep_original_and_state(client):
    row=register(client,'Hay basura acumulada en la vía pública.').json();id=row['id']
    url=f'/api/v1/admin/incidencias/{id}/analisis'
    assert client.get(url).status_code==401
    headers=credentials(client,'revisor')
    assert client.post(url).status_code==403
    first=client.post(url,headers=headers).json()
    answer={'version':1,'respuestas':{'lugar_general':'barrio Central','referencia_temporal':'desde ayer'}}
    route=f'/api/v1/admin/incidencias/{id}/aclaraciones'
    updated=client.post(route,json=answer,headers=headers)
    assert updated.status_code==200
    assert updated.json()['version']==2
    assert updated.json()['original']==first['original']
    assert updated.json()['analisis']['extraccion']['campos']['lugar_general']['origen']=='respuesta humana'
    assert not any(q['id'] in answer['respuestas'] for q in updated.json()['analisis']['preguntas'])
    assert client.post(route,json=answer,headers=headers).status_code==409
    answer['version']=2
    assert client.post(route,json=answer,headers=headers).status_code==422
    assert len(client.get(url).json())==2
    correction=client.post(f'/api/v1/admin/incidencias/{id}/extraccion',json={'version':2,'campos':{'problema_principal':None}},headers=headers)
    assert correction.status_code==200 and correction.json()['version']==3
    assert correction.json()['analisis']['extraccion']['campos']['problema_principal']['valor'] is None
    assert correction.json()['analisis']['clasificacion']==updated.json()['analisis']['clasificacion']
    assert len(client.get(url).json())==3
    with SessionLocal() as db:
        incident=db.get(Incident,id)
        assert incident.revision==1 and incident.state==row['clasificacion']['estado']
        assert incident.text==first['original']
        assert db.scalar(select(func.count()).select_from(Prediction))==1

def test_related_index_excludes_self_future_and_no_fit(client,tmp_path):
    ids=[register(client,'Hay basura acumulada en la vía pública.').json()['id'] for _ in range(3)]
    with SessionLocal() as db:
        rows=[db.get(Incident,id) for id in ids]
        start=rows[0].created_at
        for n,r in enumerate(rows):r.created_at=start+timedelta(days=n)
        db.commit();build_index(db,tmp_path)
        with patch.object(TfidfVectorizer,'fit',side_effect=AssertionError('No fit')):
            result=search_related(db,rows[1],tmp_path,10,0)
        assert result['estado']=='disponible'
        assert [i['id'] for i in result['items']]==[ids[0]]
        assert result['items'][0]['similitud_coseno']==pytest.approx(1)
        rows[0].text='Nuevo texto';db.commit()
        assert search_related(db,rows[1],tmp_path)['estado']=='no disponible'
    endpoint=f'/api/v1/admin/incidencias/{ids[1]}/relaciones'
    assert client.get(f'/api/v1/admin/incidencias/{ids[1]}/relacionados').status_code==401
    headers=credentials(client,'revisor')
    body={'relacionado_id':ids[0],'decision':'confirmar','motivo':'Mismo problema confirmado en ejercicio'}
    assert client.post(endpoint,json=body).status_code==403
    assert client.post(endpoint,json=body,headers=headers).json()['fusion_realizada'] is False
    body['relacionado_id']=ids[1]
    assert client.post(endpoint,json=body,headers=headers).status_code==422
    body['relacionado_id']=ids[2]
    assert client.post(endpoint,json=body,headers=headers).status_code==422
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Incident))==3
        assert db.scalar(select(func.count()).select_from(RelationDecision))==1

def test_experiment_audit_separates_cohorts(client,real_predictor):
    app.state.predictor=real_predictor
    assert client.get('/api/v1/admin/pln/datos').status_code==401
    credentials(client)
    d=client.get('/api/v1/admin/pln/datos').json()
    assert d['datos']['total']==86 and d['datos']['tipos']=={'elaborado':86}
    assert d['datos']['particiones']['test']==0
    cohorts={e['cohorte']:e for e in d['evaluaciones']}
    assert cohorts['test']['estado']=='No evaluado' and cohorts['test']['n'] is None
    assert cohorts['functional']['n']==8 and cohorts['challenge']['n']==14
    assert cohorts['challenge']['bloques'][0]['metricas']['n']==6
    assert d['curva_aprendizaje'] is None
    serialized=json.dumps(d)
    assert 'texto_reclamo' not in serialized and 'DEMO-C1-01' not in serialized
    absent=experimental_audit(Predictor('tests/missing.json'))
    assert absent['experimento'] is None and all(e['estado']=='No evaluado' for e in absent['evaluaciones'])
