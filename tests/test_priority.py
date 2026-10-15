import pytest
from backend.priority import prioritize
from tests.test_api import register

@pytest.mark.parametrize('text,expected',[
 ('Hay un incendio junto al mercado.','alta'),
 ('Una persona puede electrocutarse por cables expuestos.','alta'),
 ('Sin agua potable en todo el barrio.','alta'),
 ('La luminaria del barrio no enciende desde ayer.','media'),
 ('Hay basura acumulada junto a la vía.','media'),
 ('Solicito poda de un árbol del parque.','baja'),
 ('Sugiero pintar las bancas del parque.','baja'),
 ('No hay incendio ni heridos; hay basura acumulada.','media'),
 ('Sin heridos, solo sugiero pintar las bancas.','baja'),
 ('Hola.','media'),
])
def test_priorities(text,expected):
    result=prioritize(text)
    assert result['nivel']==expected and result['requiere_revision']
    assert all(e['fragmento'] in text for e in result['evidencias'])

def test_registration_and_trace_share_priority(client):
    message='Hay un incendio junto al mercado.'
    trace=client.post('/api/v1/pln/analizar',json={'descripcion':message}).json()
    saved=register(client,message).json()['clasificacion']
    assert saved['prioridad']=='alta' and saved['alerta_posible_urgencia']
    assert saved['evaluacion_prioridad']==trace['clasificacion']['evaluacion_prioridad']
    stage=next(s for s in trace['etapas'] if s['id']=='prioridad')
    assert stage['salida']==saved['evaluacion_prioridad'] and stage['tiempo_ms']>=0
