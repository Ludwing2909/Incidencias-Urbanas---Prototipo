import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from ml.data import validate,folds,split_data,agreement
from ml.inference import Predictor,LABELS
from ml.experiment import choose_threshold,evaluate,thematic_metrics,activate
from ml.text import anonymize,normalize
from backend.db import SessionLocal,Rule
from backend.services import review_reasons,urgency,classify,hints
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('category,text',[('C1','basura acumulada dentro del parque'),('C2','bache en la vereda'),('C3','semáforo sin señalización'),('C4','robo y asalto sin patrullaje'),('C5','poda del árbol y césped'),('C6','comerciante y puesto de venta'),('C7','luminaria de alumbrado apagada'),('C8','fuga de agua y desagüe sanitario')])
def test_taxonomy_limits(category,text):
    assert hints(text)=={category}

@pytest.mark.parametrize('text,reason',[('Hola','texto insuficiente'),('basura y semáforo en mal estado','varios temas'),('Quiero un certificado para mi trámite','fuera de alcance'),('Please fix the broken street','idioma no soportado'),('Jani waliki maypi','idioma no soportado'),('Los unicornios bailan sobre las nubes','fuera de alcance')])
def test_review_reasons(text,reason):assert reason in review_reasons(text)

@pytest.mark.parametrize('text,expected',[('Hay un incendio junto al mercado',True),('No hay incendio, solo residuos',False),('Sin heridos en el lugar',False),('Puede electrocutarse alguien con la luminaria',True),('Todo podría venirse abajo de repente',False)])
def test_urgency_limits(text,expected):assert urgency(text)[0] is expected

def test_redaction_preserves_negation_accents():
    text='No pasó el camión. DNI 12345678, teléfono 987654321, correo vecino@example.com.'
    clean=anonymize(text)
    assert '12345678' not in clean and '987654321' not in clean and 'vecino@' not in clean
    assert 'No pasó el camión' in clean
    assert normalize('  cañón\n roto  ')=='cañón roto'

def test_demo_contract_and_folds():
    frame=validate(ROOT/'data/demostracion.csv')
    train=frame[frame.particion.eq('train')]
    for a,b in folds(train):
        assert not set(train.iloc[a].grupo_origen)&set(train.iloc[b].grupo_origen)
        assert set(train.iloc[a].categoria)==set(LABELS)
        assert set(train.iloc[b].categoria)==set(LABELS)

@pytest.mark.parametrize('mutation',['ninth','exact_duplicate','near_duplicate','leak','synthetic_test','unvalidated'])
def test_invalid_datasets(tmp_path,mutation):
    frame=pd.read_csv(ROOT/'data/demostracion.csv',dtype=str,keep_default_na=False)
    if mutation=='ninth':frame.loc[0,'categoria']='R9'
    elif mutation=='exact_duplicate':frame.loc[1,'texto_reclamo']=frame.loc[0,'texto_reclamo']
    elif mutation=='near_duplicate':frame.loc[1,'texto_reclamo']=frame.loc[0,'texto_reclamo']+' ahora'
    elif mutation=='leak':frame.loc[1,'grupo_origen']=frame.loc[0,'grupo_origen'];frame.loc[1,'particion']='functional'
    elif mutation=='synthetic_test':frame.loc[0,'particion']='test'
    else:frame.loc[0,'validado']='false'
    path=tmp_path/'invalid.csv';frame.to_csv(path,index=False)
    with pytest.raises(ValueError):validate(path)

def test_cv_fails_insufficient_groups():
    frame=validate(ROOT/'data/demostracion.csv')
    train=frame[frame.particion.eq('train')].copy();train.grupo_origen=train.categoria
    with pytest.raises(ValueError,match='dos grupos'):folds(train)

def test_split_reproducible(tmp_path):
    first=split_data(ROOT/'data/demostracion.csv',tmp_path/'a.csv')
    second=split_data(ROOT/'data/demostracion.csv',tmp_path/'b.csv')
    assert first==second
    assert 'test' not in first['partitions'] and 'validation' not in first['partitions']

def test_agreement_before_adjudication(tmp_path):
    path=tmp_path/'annotations.csv'
    pd.DataFrame({'id':['a','b','c','d'],'anotador_a':['C1','C2','C1','C2'],'anotador_b':['C1','C2','C2','C2']}).to_csv(path,index=False)
    result=agreement(path)
    assert result['agreement']==.75 and result['cohen_kappa']==.5

class FakePredictor:
    def __init__(self,topic='C1',score=.98,kind='probabilidad_calibrada',threshold=.8):
        self.topic,self.score,self.kind=topic,score,kind
        self.manifest={'threshold':threshold,'threshold_validated_real':True,'version':'test','threshold_version':'test-v1','demonstration':False}
    def predict(self,text):return self.topic,self.score,self.kind

@pytest.mark.parametrize('topic,score,kind,validated,reason',[('C1',.4,'probabilidad_calibrada',True,'baja puntuación'),('C1',5,'margen',True,'puntuación no probabilística o sin calibración'),('C1',.98,'probabilidad_calibrada',False,'competencia no validada'),('C7',.98,'probabilidad_calibrada',True,'competencia no validada'),('C8',.98,'probabilidad_calibrada',True,'competencia no validada')])
def test_review_policy(topic,score,kind,validated,reason):
    with SessionLocal() as db:
        db.add(Rule(category=topic,territory='Juliaca urbana',destination='Destino de prueba',conditions='incidencia urbana',validated=validated,valid_from='2020-01-01',valid_until='2099-01-01',source='Fuente documental prueba',responsible='Equipo de prueba'))
        db.commit()
        text={'C1':'Hay mucha basura acumulada junto al barrio','C7':'La luminaria del barrio permanece apagada','C8':'Hay una fuga de agua en la vía'}[topic]
        result,_=classify(db,FakePredictor(topic,score,kind),text)
        assert result['requiere_revision'] and reason in result['motivos_revision']

def test_rule_missing_and_enabled_suggestion():
    with SessionLocal() as db:
        result,_=classify(db,FakePredictor(),'Hay basura acumulada en la esquina')
        assert 'regla inexistente' in result['motivos_revision']
        db.add(Rule(category='C1',territory='Juliaca urbana',destination='Destino de prueba',conditions='incidencia urbana',validated=True,valid_from='2020-01-01',valid_until='2099-01-01',source='Fuente documental prueba',responsible='Responsable prueba'))
        db.commit()
        result,_=classify(db,FakePredictor(),'Hay basura acumulada en la esquina')
        assert result['estado']=='Sugerencia disponible' and not result['requiere_revision']

def test_missing_or_incompatible_model(tmp_path):
    assert Predictor(tmp_path/'missing.json').model is None
    path=tmp_path/'bad.json';path.write_text(json.dumps({'labels':['R9'],'artifact':'bad.joblib'}))
    assert Predictor(path).model is None

def test_script_api_prediction_consistent(client):
    manifest=ROOT/'models/active.json'
    if not manifest.exists():pytest.skip('Modelo demo todavía no entrenado')
    p=Predictor(manifest);assert p.model is not None
    client.app.state.predictor=p
    text='La luminaria del barrio no enciende durante la noche.'
    from tests.test_api import register
    api_result=register(client,text).json()['clasificacion']
    topic,score,kind=p.predict(text)
    assert api_result['tema']==topic and api_result['puntuacion']==pytest.approx(score)
    assert api_result['tipo_puntuacion']==kind and api_result['requiere_revision']

def test_artifact_hash_and_dependency_guard(tmp_path):
    source=ROOT/'models/active.json'
    if not source.exists():pytest.skip('Modelo demo todavía no entrenado')
    meta=json.loads(source.read_text());meta['sha256']='0'*64
    (tmp_path/'pipeline.joblib').write_bytes(b'not-a-pickle')
    meta['artifact']='pipeline.joblib'
    path=tmp_path/'manifest.json';path.write_text(json.dumps(meta))
    assert Predictor(path).model is None
    meta['dependencies']['scikit-learn']='0.0.0';path.write_text(json.dumps(meta))
    assert Predictor(path).model is None
