import json
from pathlib import Path
import shutil
import pandas as pd
import pytest
from ml.experiment import evaluate,choose_threshold
from ml.inference import Predictor
from ml.data import sha
ROOT=Path(__file__).resolve().parents[1]

def test_policy_report_and_null_denominators(tmp_path):
    source_run=ROOT/'reports/runs/demo-v3'
    if not source_run.exists():pytest.skip('Requiere ejecutar primero demostración')
    run=tmp_path/'run';run.mkdir()
    for name in ['manifest.json','pipeline.joblib','baseline_dummy.joblib','baseline_keywords.joblib']:
        shutil.copy2(source_run/name,run/name)
    result=evaluate(ROOT/'data/demo_particionado.csv',run,'challenge')
    assert result['n']==14 and result['review']['coverage']==0
    assert result['review']['selective_error'] is None
    assert result['review']['destination_reference_n']==0
    assert result['review']['rules_hash']==sha(ROOT/'config/demo_rules.json')
    assert len(result['coverage_error_curve'])==10
    with pytest.raises(ValueError,match='ya evaluada'):evaluate(ROOT/'data/demo_particionado.csv',run,'challenge')

def test_threshold_freeze_and_no_real_validation(tmp_path):
    source_run=ROOT/'reports/runs/demo-v3'
    if not source_run.exists():pytest.skip('Requiere ejecutar primero demostración')
    run=tmp_path/'run';run.mkdir()
    meta=json.loads((source_run/'manifest.json').read_text(encoding='utf-8'))
    meta['threshold_version']=None
    (run/'manifest.json').write_text(json.dumps(meta),encoding='utf-8')
    result=choose_threshold(ROOT/'data/demo_particionado.csv',run)
    assert result['all_review'] and result['selected'] is None and result['validation_rows']==0
    with pytest.raises(ValueError,match='congelado'):choose_threshold(ROOT/'data/demo_particionado.csv',run)

def test_model_runtime_error_still_saves(client):
    class Broken:
        manifest={}
        def predict(self,text):raise ValueError('Inference failure')
    client.app.state.predictor=Broken()
    from tests.test_api import register
    response=register(client)
    assert response.status_code==201
    result=response.json()['clasificacion']
    assert result['tema'] is None and 'modelo no disponible' in result['motivos_revision']
