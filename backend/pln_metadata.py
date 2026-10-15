"""Proyecciones agregadas: nunca expone textos/IDs del corpus."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from backend.settings import ROOT
from ml.trace import model_description


def read_json(path):
    try:
        if path.stat().st_size > 5_000_000:
            return None
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def public_metadata(predictor):
    m = predictor.manifest
    return {'version':m.get('version'),'disponible':predictor.model is not None,
        'demostrativo':m.get('demonstration'),'umbral':m.get('threshold'),
        'umbral_validado_real':m.get('threshold_validated_real',False),
        'modelo':model_description(predictor.model),'limites':m.get('limitations',[]),
        'operaciones':'Inferencia: no ajusta el modelo ni registra incidencias'}


def dataset_summary(meta):
    expected = meta.get('dataset_sha256')
    for path in sorted((ROOT/'data').glob('*.csv')):
        if not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            continue
        with path.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        if not rows or 'texto_reclamo' not in rows[0]:
            continue
        counts = Counter((r['particion'],r['tipo_dato'],r['categoria'],r['fuente']) for r in rows)
        groups = {}
        for r in rows:
            groups.setdefault(r['grupo_origen'],set()).add(r['particion'])
        texts = Counter(' '.join(r['texto_reclamo'].lower().split()) for r in rows)
        partition_groups = {p:len({r['grupo_origen'] for r in rows if r['particion']==p}) for p in ('train','validation','test','functional','challenge')}
        # Procedencia identificada por hash, no por el nombre de una entrega.
        source_meta = None
        for manifest in (ROOT/'data').glob('*manifest.json'):
            candidate = read_json(manifest)
            if candidate and candidate.get('sha256') == expected:
                source_meta = {k:candidate.get(k) for k in ('method','generator_version','real_rows','linguistic_local_review')}
                break
        return {'estado':'disponible','version_hash':expected,'total':len(rows),
            'tipos':dict(Counter(r['tipo_dato'] for r in rows)),
            'particiones':{p:sum(r['particion']==p for r in rows) for p in partition_groups},
            'distribucion':[dict(particion=p,tipo_dato=t,categoria=c or None,fuente=s,n=n) for (p,t,c,s),n in sorted(counts.items())],
            'grupos_por_particion':partition_groups,'grupos_compartidos':sum(len(ps)>1 for ps in groups.values()),
            'duplicados_exactos':sum(n-1 for n in texts.values()),'procedencia':source_meta,
            'anotacion_independiente':'No documentada en el manifiesto' if not source_meta or 'no doble' in (source_meta.get('method') or '') else 'Consultar protocolo y reporte de acuerdo',
            'control':'El validador de entrenamiento controla duplicados cercanos y grupos. Esta vista solo recalcula duplicados exactos y cruces de partición; no certifica equivalencia semántica.'}
    return {'estado':'no disponible','motivo':'No se encontró un CSV local cuyo hash coincida con el artefacto activo'}


def experimental_audit(predictor):
    meta = predictor.manifest
    version = meta.get('version')
    base = ROOT/'reports/runs'
    run = base/str(version)
    if run.parent.resolve() != base.resolve():
        run = base/'__missing__'
    manifest = read_json(run/'manifest.json')
    compatible = bool(manifest and manifest.get('sha256')==meta.get('sha256') and manifest.get('dataset_sha256')==meta.get('dataset_sha256'))
    experiment = read_json(run/'experiment.json') if compatible else None
    if experiment and (experiment.get('version')!=version or experiment.get('dataset_hash')!=meta.get('dataset_sha256')):
        experiment=None
    evaluations = []
    for partition,filename in [('test','evaluation.json'),('functional','functional_evaluation.json'),('challenge','challenge_evaluation.json')]:
        report = read_json(run/filename) if compatible else None
        if not report:
            evaluations.append({'cohorte':partition,'estado':'No evaluado','n':None,'bloques':[]})
            continue
        blocks=[]
        for block in report.get('results',[]):
            metrics=block.get('classification',{})
            blocks.append({'tipo_dato':block.get('tipo_dato'),'fuente':block.get('fuente'),'cohort_n':block.get('cohort_n'),
                'metricas':metrics,'errores_n':len(block.get('errors',[]))})
        evaluations.append({'cohorte':partition,'estado':'Evaluado','n':report.get('n'),
            'fecha_evaluacion':report.get('evaluated_at'),
            'fecha_archivo': 'La ejecución antigua no registra fecha de evaluación' if not report.get('evaluated_at') else None,
            'bloques':blocks,'referencias':report.get('baselines',{}),'revision':report.get('review'),
            'curva_cobertura':report.get('coverage_error_curve',[])})
    return {'modelo':public_metadata(predictor),'datos':dataset_summary(meta),
        'experimento':experiment,'fecha_entrenamiento':meta.get('created_at'),
        'pliegues':meta.get('folds'),'esquema':'StratifiedGroupKFold; índices explícitos del entrenamiento',
        'calibracion':meta.get('calibration'),'evaluaciones':evaluations,
        'umbral':read_json(run/'threshold.json') if compatible else None,
        'curva_aprendizaje':read_json(run/'learning_curve.json') if compatible else None,
        'advertencias':['Las métricas CV son de desarrollo; no rendimiento local de Juliaca.',
            'Casos funcionales y desafíos elaborados no sustituyen una prueba real independiente.',
            'svc es el identificador histórico de LinearSVC; el estimador concreto se lee del artefacto.',
            'Un reporte ausente no se convierte en cero. No se calculan experimentos en esta petición.']}


def capabilities():
    return read_json(ROOT/'config/pln_capabilities.json') or []
