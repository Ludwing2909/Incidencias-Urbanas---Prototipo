import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from backend.db import SessionLocal,Incident,Prediction,Review,Audit,Rule,engine
from backend.main import app
from backend.schemas import Registration
from tests.conftest import credentials

def register(client,text='Hay basura acumulada por falta de recojo en la vía pública.',key=None):
    return client.post('/api/v1/incidencias',json={'descripcion':text},headers={'Idempotency-Key':key or str(uuid4())})

def test_register_missing_model_and_follow(client):
    r=register(client);assert r.status_code==201
    body=r.json();Registration.model_validate(body)
    assert body['clasificacion']['tema'] is None
    assert body['clasificacion']['puntuacion'] is None
    assert body['clasificacion']['estado']=='Pendiente de revisión'
    assert 'modelo no disponible' in body['clasificacion']['motivos_revision']
    tracked=client.post('/api/v1/seguimiento/consulta',json={'codigo':body['codigo'],'secreto':body['secreto_seguimiento']})
    assert tracked.status_code==200
    assert set(tracked.json())=={'codigo','estado','fecha','cronologia'}
    assert 'texto' not in tracked.json()
    with SessionLocal() as db:
        row=db.get(Incident,body['id'])
        assert row.secret_hash != body['secreto_seguimiento']

@pytest.mark.parametrize('text',['','   ','\n\t','x'*3001])
def test_invalid_input(client,text):
    assert register(client,text).status_code==422
    with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(Incident))==0

def test_short_is_saved_for_review(client):
    assert 'texto insuficiente' in register(client,'Auxilio').json()['clasificacion']['motivos_revision']

def test_idempotency_and_concurrent_sequences(client):
    key=str(uuid4())
    first=register(client,key=key).json()
    second=register(client,key=key)
    assert second.status_code==200 and second.json()==first
    assert register(client,'Otra descripción diferente sobre la vía.',key).status_code==409
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses=list(pool.map(lambda _:register(client),range(12)))
    assert all(r.status_code==201 for r in responses)
    codes=[r.json()['codigo'] for r in responses]
    assert len(set(codes))==12
    concurrent_key=str(uuid4())
    with ThreadPoolExecutor(max_workers=4) as pool:
        repeated=list(pool.map(lambda _:register(client,key=concurrent_key),range(4)))
    assert all(r.status_code in (200,201) for r in repeated)
    assert len({r.json()['id'] for r in repeated})==1

def test_wrong_secret_does_not_reveal_existence(client):
    body=register(client).json()
    responses=[client.post('/api/v1/seguimiento/consulta',json={'codigo':code,'secreto':'invalid-secret-123456789'}) for code in [body['codigo'],'REC-2026-99999']]
    assert all(r.status_code==404 for r in responses)
    assert responses[0].json()==responses[1].json()

def test_permissions_csrf_logout_and_audit(client):
    body=register(client).json();id=body['id']
    assert client.get('/api/v1/admin/incidencias').status_code==401
    headers=credentials(client,'revisor')
    review={'tema':'C2','destino':'Destino revisado académico','motivo':'Corrección manual de tema para ejercicio','version':1}
    url=f'/api/v1/admin/incidencias/{id}/revision'
    assert client.post(url,json=review).status_code==403
    assert client.post(url,json=review,headers=headers).status_code==200
    assert client.post(url,json=review,headers=headers).status_code==409
    detail=client.get(f'/api/v1/admin/incidencias/{id}').json()
    assert detail['prediccion']['tema'] is None and detail['current_topic']=='C2'
    assert detail['revisiones'][0]['original_topic'] is None
    transition={'estado':'Derivado','motivo':'Actuación humana de demostración','version':2,'confirmacion_humana':True,'evidencia':'Referencia académica demostrativa'}
    assert client.post(f'/api/v1/admin/incidencias/{id}/transiciones',json=transition,headers=headers).status_code==403
    assert client.post('/api/v1/admin/reglas',json={},headers=headers).status_code==403
    assert client.post('/api/v1/auth/logout',headers=headers).status_code==204
    assert client.get('/api/v1/admin/incidencias').status_code==401
    with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(Audit))==2

def test_transitions_evidence_and_reopening(client):
    row=register(client).json();id=row['id'];headers=credentials(client)
    url=f'/api/v1/admin/incidencias/{id}/transiciones'
    t={'estado':'Resuelto','motivo':'No corresponde saltar estados','version':1}
    assert client.post(url,json=t,headers=headers).status_code==409
    assert client.post(f'/api/v1/admin/incidencias/{id}/revision',json={'tema':'C1','destino':'Destino confirmado','motivo':'Revisión manual documentada','version':1},headers=headers).status_code==200
    t.update(estado='Derivado',version=2)
    assert client.post(url,json=t,headers=headers).status_code==422
    t.update(confirmacion_humana=True,evidencia='Acta de ejercicio académico')
    assert client.post(url,json=t,headers=headers).status_code==200
    assert client.post(f'/api/v1/admin/incidencias/{id}/revision',json={'tema':'C3','destino':None,'motivo':'Cambio improcedente sin reapertura','version':3},headers=headers).status_code==409
    t.update(estado='Resuelto',version=3)
    assert client.post(url,json=t,headers=headers).status_code==200
    t.update(estado='Pendiente de revisión',version=4)
    assert client.post(url,json=t,headers=headers).status_code==200

def test_rule_versions_are_immutable(client):
    headers=credentials(client)
    body={'category':'C1','territory':'Juliaca urbana','destination':'Destino de demostración','conditions':'incidencia urbana','validated':False,'valid_from':'2026-01-01','valid_until':'2027-12-31','source':'Referencia elaborada sin validar','responsible':'Equipo académico','version':1}
    created=client.post('/api/v1/admin/reglas',json=body,headers=headers)
    assert created.status_code==201
    id=created.json()['id'];body.update(destination='Destino revisado')
    changed=client.patch(f'/api/v1/admin/reglas/{id}',json=body,headers=headers)
    assert changed.status_code==200 and changed.json()['version']==2
    rules=client.get('/api/v1/admin/reglas').json()
    assert len(rules)==2 and sum(r['active'] for r in rules)==1
    assert next(r for r in rules if r['id']==id)['destination']=='Destino de demostración'

def test_rate_limit(client):
    for _ in range(10):
        assert client.post('/api/v1/auth/login',json={'usuario':'no-user','password':'wrong'}).status_code==401
    assert client.post('/api/v1/auth/login',json={'usuario':'no-user','password':'wrong'}).status_code==429

def test_restart_and_openapi(client):
    row=register(client).json()
    engine.dispose()
    with TestClient(app) as restarted:
        assert restarted.post('/api/v1/seguimiento/consulta',json={'codigo':row['codigo'],'secreto':row['secreto_seguimiento']}).status_code==200
    schema=client.get('/openapi.json').json()
    assert schema['components']['schemas']['Classification']['properties']['tema']
    assert len(schema['components']['schemas']['Classification']['properties']['tema']['anyOf'][0]['enum'])==8
    assert client.get('/api/v1/health/ready').status_code==200
    assert client.get('/api/v1/categorias').json()['categorias'].keys()=={f'C{i}' for i in range(1,9)}
