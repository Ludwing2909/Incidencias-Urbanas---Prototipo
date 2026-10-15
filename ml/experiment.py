import importlib.metadata
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, log_loss, make_scorer
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC, SVC
from ml.data import validate, folds, sha
from ml.inference import LABELS
from ml.text import anonymize

ROOT = Path(__file__).resolve().parents[1]

class KeywordClassifier(ClassifierMixin,BaseEstimator):
    def fit(self,X,y):
        self.classes_ = np.array(LABELS)
        self.keywords_ = json.loads((ROOT/'config/keywords.json').read_text(encoding='utf-8'))
        return self
    def predict(self,X):
        # Empate/ninguna coincidencia -> C1 solo para referencia temática sin abstención.
        return np.array([max(LABELS,key=lambda c:sum(w in t.lower() for w in self.keywords_[c])) for t in X])

def pipeline(estimator):
    return Pipeline([('tfidf',TfidfVectorizer(preprocessor=anonymize,lowercase=True,strip_accents=None)),('classifier',estimator)])

def train(source, output, seed=42, mode='hybrid', demo=False, expanded=False):
    frame = validate(source)
    train_frame = frame[frame.particion.eq('train')].copy()
    if mode == 'real':
        train_frame = train_frame[train_frame.tipo_dato.eq('real')]
    if not demo and train_frame.tipo_dato.eq('real').sum() == 0:
        raise ValueError('No hay entrenamiento real; use --demo para la demostración identificada')
    cv = folds(train_frame,seed=seed)
    X,y = train_frame.texto_reclamo.to_numpy(),train_frame.categoria.to_numpy()
    scorer = make_scorer(f1_score,labels=LABELS,average='macro',zero_division=0,pos_label=None)
    specs = [
        ('dummy',pipeline(DummyClassifier(strategy='most_frequent')),{}),
        ('keywords',KeywordClassifier(),{}),
        ('logistic',pipeline(LogisticRegression(max_iter=2000,random_state=seed)),{'tfidf__ngram_range':[(1,1),(1,2)],'classifier__C':[.1,1,10],'classifier__class_weight':[None,'balanced']}),
        ('svc',pipeline(LinearSVC(random_state=seed)),{'tfidf__ngram_range':[(1,1),(1,2)],'classifier__C':[.1,1,10],'classifier__class_weight':[None,'balanced']}),
        ('nb',pipeline(MultinomialNB()),{'tfidf__ngram_range':[(1,1),(1,2)],'classifier__alpha':[.1,1]}),
    ]
    if expanded:
        # Búsqueda acotada offline. Conserva el identificador histórico svc=LinearSVC.
        specs.append(('svm_rbf',pipeline(SVC(kernel='rbf',random_state=seed)),{'classifier__C':[.1,1],'classifier__class_weight':[None,'balanced']}))
        updated=[]
        for name, estimator, params in specs:
            if name in ('dummy','keywords'):
                updated.append((name,estimator,params));continue
            base={k:v for k,v in params.items() if not k.startswith('tfidf__')}
            # 2 C/alpha × 2 pesos cuando corresponda × 2 representaciones.
            if 'classifier__C' in base:base['classifier__C']=[.1,1]
            grids=[{**base,'tfidf__analyzer':['word'],'tfidf__ngram_range':[(1,2)]},
                   {**base,'tfidf__analyzer':['char_wb'],'tfidf__ngram_range':[(3,5)]}]
            updated.append((name,estimator,grids))
        specs=updated
    output = Path(output)
    if output.exists():
        raise ValueError('Use un directorio nuevo para conservar ejecuciones previas')
    output.mkdir(parents=True)
    results, candidates, calibrations = [], [], {}
    for name, estimator, params in specs:
        started = time.perf_counter()
        search = GridSearchCV(estimator,params,cv=cv,scoring=scorer,n_jobs=1,error_score='raise',return_train_score=False)
        search.fit(X,y)
        pd.DataFrame(search.cv_results_).to_csv(output/f'{name}_cv.csv',index=False)
        concrete=type(search.best_estimator_.steps[-1][1]).__name__ if isinstance(search.best_estimator_,Pipeline) else type(search.best_estimator_).__name__
        result = {'model':name,'estimator':concrete,'cv_macro_f1':float(search.best_score_),'params':search.best_params_,'seconds':time.perf_counter()-started}
        results.append(result)
        if name in ('logistic','svc','nb','svm_rbf'):
            candidates.append((float(search.best_score_),name,search.best_estimator_))
            # Índices explícitos relativos a X/y del subconjunto de entrenamiento correcto.
            calibrated = CalibratedClassifierCV(search.best_estimator_,method='sigmoid',cv=cv,ensemble=True,n_jobs=1)
            calibrated.fit(X,y)
            calibrations[name] = calibrated
    # Orden de simplicidad documentado: logística, SVC, NB si empate numérico.
    rank = {'logistic':0,'svc':1,'nb':2,'svm_rbf':3}
    candidates.sort(key=lambda item:(-round(item[0],8),rank[item[1]]))
    best_score,name,_ = candidates[0]
    selected = calibrations[name]
    joblib.dump(selected,output/'pipeline.joblib')
    version = output.name
    dependencies = {p:importlib.metadata.version(p) for p in ['scikit-learn','numpy','joblib','pandas','scipy']}
    meta = {'version':version,'artifact':'pipeline.joblib','sha256':sha(output/'pipeline.joblib'),'labels':LABELS,
        'dependencies':dependencies,'created_at':datetime.now(timezone.utc).isoformat(),'seed':seed,
        'dataset_sha256':sha(source),'category_version':'C1-C8-v1','rules_version':'independientes-de-modelo',
        'keyword_sha256':sha(ROOT/'config/keywords.json'),'model':name,'params':next(r['params'] for r in results if r['model']==name),
        'training_mode':mode,'demonstration':demo,'training_rows':len(X),'training_groups':int(train_frame.grupo_origen.nunique()),
        'candidate_names':list(calibrations),'expanded_search':expanded,'cv_schema':'StratifiedGroupKFold',
        'folds':len(cv),'calibration':'sigmoid explicit group folds','threshold':None,'threshold_version':None,
        'threshold_validated_real':False,'frozen':True,'metrics':{'cv_macro_f1':best_score},
        'train_ids':train_frame.id.tolist(),'train_groups':sorted(set(train_frame.grupo_origen)),
        'cv_fold_ids':[{'train':train_frame.iloc[a].id.tolist(),'calibration':train_frame.iloc[b].id.tolist()} for a,b in cv],
        'limitations':['Demostración no acredita rendimiento local' if demo else 'Pendiente de prueba independiente','Umbral sin validación real bloquea sugerencias']}
    for calibration_name,model in calibrations.items():
        joblib.dump(model,output/f'calibrated_{calibration_name}.joblib')
    for baseline_name,estimator,_ in specs[:2]:
        estimator.fit(X,y)
        joblib.dump(estimator,output/f'baseline_{baseline_name}.joblib')
    experiment = {'version':version,'dataset_hash':sha(source),'seed':seed,'demonstration':demo,'mode':mode,'results':results,'selected':name,'selection':'CV de entrenamiento por grupos; macro-F1; empate por simplicidad','calibration':'sigmoid; grupos solo de entrenamiento','test_used':False,'dependencies':dependencies,'created_at':meta['created_at'],'expanded_search':expanded,'search_grids':{n:p for n,_,p in specs}}
    (output/'manifest.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    (output/'experiment.json').write_text(json.dumps(experiment,indent=2,ensure_ascii=False),encoding='utf-8')
    return experiment

def wilson(success,total,z=1.96):
    if not total:
        return None
    p = success/total
    d = 1+z*z/total
    center = (p+z*z/(2*total))/d
    spread = z*np.sqrt((p*(1-p)+z*z/(4*total))/total)/d
    return [max(0.,center-spread),min(1.,center+spread)]

def check_dataset(meta,frame,path):
    if sha(path) != meta['dataset_sha256']:
        raise ValueError('Dataset cambió desde el entrenamiento; genere nueva ejecución')
    if set(frame.loc[frame.particion.ne('train'),'grupo_origen']) & set(meta['train_groups']):
        raise ValueError('Fuga de grupos frente al entrenamiento')

def choose_threshold(source, run):
    run = Path(run)
    meta = json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    if (run/'evaluation.json').exists() or meta.get('test_evaluated'):
        raise ValueError('Prueba ya evaluada; no modificar el umbral')
    if meta.get('threshold_version'):
        raise ValueError('Umbral congelado; use una nueva ejecución')
    frame = validate(source)
    check_dataset(meta,frame,source)
    validation = frame[frame.particion.eq('validation') & frame.tipo_dato.eq('real') & frame.categoria.ne('')]
    adequate = len(validation) >= 40 and set(validation.categoria) == set(LABELS) and validation.grupo_origen.nunique() >= 16
    rows = []
    if adequate and not meta['demonstration']:
        model = joblib.load(run/'pipeline.joblib')
        p = model.predict_proba(validation.texto_reclamo)
        ypred = model.classes_[p.argmax(axis=1)]
        correct = ypred == validation.categoria.to_numpy()
        for threshold in np.round(np.arange(.50,.951,.05),2):
            accepted = p.max(axis=1) >= threshold
            n = int(accepted.sum())
            success = int(correct[accepted].sum())
            rows.append({'threshold':round(float(threshold),2),'accepted':n,'total':len(validation),'coverage':n/len(validation),'selective_accuracy':success/n if n else None,'wilson_95':wilson(success,n)})
        # Meta de precisión empírica; incertidumbre se muestra, nunca garantía.
        eligible = [r for r in rows if r['accepted'] and r['selective_accuracy'] >= .9]
        chosen = max(eligible,key=lambda r:(r['coverage'],-r['threshold'])) if eligible else None
        meta['threshold'] = chosen['threshold'] if chosen else None
        meta['threshold_validated_real'] = chosen is not None
        meta['metrics']['threshold_validation'] = chosen
        meta['validation_ids'] = validation.id.tolist()
        calibration = {}
        for name in meta.get('candidate_names',('logistic','svc','nb')):
            model = joblib.load(run/f'calibrated_{name}.joblib')
            pp = model.predict_proba(validation.texto_reclamo)
            yy = np.array([LABELS.index(c) for c in validation.categoria])
            target = np.eye(8)[yy]
            calibration[name] = {'log_loss':float(log_loss(validation.categoria,pp,labels=LABELS)),'multiclass_brier':float(np.mean(np.sum((pp-target)**2,axis=1)))}
        (run/'calibration.json').write_text(json.dumps(calibration,indent=2),encoding='utf-8')
    else:
        meta['threshold'] = None
        meta['threshold_validated_real'] = False
    meta['threshold_version'] = meta['version']+'-threshold-v1'
    report = {'validation_rows':len(validation),'adequate':adequate,'minimum_policy':'40 textos reales, 8 clases, 16 grupos: control de ingeniería, no suficiencia estadística','thresholds':rows,'selected':meta['threshold'],'all_review':meta['threshold'] is None,'uncertainty':'Wilson asume casos independientes; agrupación puede ampliar incertidumbre'}
    (run/'threshold.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    (run/'manifest.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    return report

def thematic_metrics(model,frame):
    y = frame.categoria
    pred = model.predict(frame.texto_reclamo)
    report = classification_report(y,pred,labels=LABELS,output_dict=True,zero_division=0)
    for label in LABELS:
        report[label]['evaluated'] = bool((y==label).sum())
        if not report[label]['evaluated']:
            report[label].update(precision=None,recall=None,**{'f1-score':None})
    present = [c for c in LABELS if (y==c).any()]
    return {'n':len(frame),'accuracy':float(accuracy_score(y,pred)),
        'macro_f1_present_classes':float(f1_score(y,pred,labels=present,average='macro',zero_division=0)),
        'all_eight_evaluated':len(present)==8,'classification_report':report,
        'confusion_matrix':confusion_matrix(y,pred,labels=LABELS).tolist(),'labels':LABELS}, pred

def evaluate(source,run,partition='test',rules_path=None,destination_reference=None):
    run = Path(run)
    meta = json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    if not meta['threshold_version']:
        raise ValueError('Congele primero el umbral, aunque sea nulo')
    output_name = 'evaluation.json' if partition == 'test' else f'{partition}_evaluation.json'
    if (run/output_name).exists():
        raise ValueError('Cohorte ya evaluada; no reutilizar test para ajustar')
    frame = validate(source)
    check_dataset(meta,frame,source)
    cohort = frame[frame.particion.eq(partition)]
    if cohort.empty:
        report = {'partition':partition,'n':0,'status':'no calculable; no hay cohorte','results':[]}
        (run/output_name).write_text(json.dumps(report,indent=2),encoding='utf-8')
        return report
    model = joblib.load(run/'pipeline.joblib')
    results = []
    for (kind,source_name),block in cohort.groupby(['tipo_dato','fuente']):
        known = block[block.categoria.ne('')]
        metrics,pred = thematic_metrics(model,known) if not known.empty else ({'n':0},[])
        errors = [{'id':r.id,'expected':r.categoria,'predicted':str(p)} for (_,r),p in zip(known.iterrows(),pred) if r.categoria != p]
        results.append({'tipo_dato':kind,'fuente':source_name,'cohort_n':len(block),'classification':metrics,'errors':errors})
    from backend.services import review_reasons,select_rule,classification_result
    from types import SimpleNamespace
    rules_path=Path(rules_path) if rules_path else ROOT/'config/demo_rules.json'
    rules=[SimpleNamespace(**{**r,'id':r.get('id',f'file-rule-{i}')}) for i,r in enumerate(json.loads(rules_path.read_text(encoding='utf-8')))]
    pp = model.predict_proba(cohort.texto_reclamo)
    topics = model.classes_[pp.argmax(axis=1)]
    scoring_accept = (pp.max(axis=1) >= meta['threshold']) if meta['threshold'] is not None else np.zeros(len(cohort),dtype=bool)
    structural = np.array([not review_reasons(t) for t in cohort.texto_reclamo])
    competition = np.isin(topics,['C7','C8'])
    decisions=[classification_result(str(topic),float(prob.max()),'probabilidad_calibrada',meta,row.texto_reclamo,select_rule(rules,str(topic),row.get('ubicacion_general',None))) for (_,row),topic,prob in zip(cohort.iterrows(),topics,pp)]
    accepted = np.array([not d['requiere_revision'] for d in decisions])
    known = cohort.categoria.ne('').to_numpy()
    outside = cohort.motivo_revision.str.contains('fuera de alcance').to_numpy()
    known_accepted=accepted&known
    destination_n,destination_matches=0,0
    if destination_reference:
        reference=pd.read_csv(destination_reference,dtype=str,keep_default_na=False)
        if not {'id','destino_referencia','validado_admin'}.issubset(reference.columns) or reference.id.duplicated().any():
            raise ValueError('Referencia administrativa requiere id único, destino_referencia, validado_admin')
        refs={r.id:r.destino_referencia for _,r in reference.iterrows() if r.validado_admin=='true' and r.destino_referencia}
        for (_,row),decision in zip(cohort.iterrows(),decisions):
            if row.id in refs:
                destination_n+=1
                destination_matches+=decision['destino_sugerido']==refs[row.id]
    selective = {'cohort_n':len(cohort),'enabled':int(accepted.sum()),'coverage':float(accepted.mean()),'known_accepted':int(known_accepted.sum()),
        'selective_error':float(((topics!=cohort.categoria.to_numpy())&known_accepted).sum()/known_accepted.sum()) if known_accepted.sum() else None,
        'outside_n':int(outside.sum()),'false_outside_acceptance':float((accepted&outside).sum()/outside.sum()) if outside.sum() else None,
        'destination_agreement':destination_matches/destination_n if destination_n else None,'destination_reference_n':destination_n,
        'score_abstention':int((~scoring_accept).sum()),
        'competence_abstention':sum(any(r in d['motivos_revision'] for r in ['regla inexistente','competencia no validada']) for d in decisions),
        'c7_c8':int(competition.sum()),'rules_hash':sha(rules_path),
        'explanation':'Política común a API e inferencia; destino necesita referencia administrativa independiente'}
    curve=[]
    for threshold in np.round(np.arange(.5,.951,.05),2):
        hypothetical=(pp.max(axis=1)>=threshold)&structural&~competition
        known_accepted=hypothetical&known
        wrong=(topics != cohort.categoria.to_numpy()) & known_accepted
        candidate_meta={**meta,'threshold':float(threshold)}
        operational=np.array([not classification_result(str(topic),float(prob.max()),'probabilidad_calibrada',candidate_meta,row.texto_reclamo,select_rule(rules,str(topic),row.get('ubicacion_general',None)))['requiere_revision'] for (_,row),topic,prob in zip(cohort.iterrows(),topics,pp)])
        curve.append({'threshold':round(float(threshold),2),'score_only_coverage':float((pp.max(axis=1)>=threshold).mean()),
            'hypothetical_without_rule_block_coverage':float(hypothetical.mean()),'known_accepted':int(known_accepted.sum()),
            'hypothetical_selective_error':float(wrong.sum()/known_accepted.sum()) if known_accepted.sum() else None,'operational_coverage':float(operational.mean())})
    baselines={}
    known_frame=cohort[cohort.categoria.ne('')]
    if not known_frame.empty:
        for name in ('dummy','keywords'):
            baselines[name]=thematic_metrics(joblib.load(run/f'baseline_{name}.joblib'),known_frame)[0]
    report={'partition':partition,'n':len(cohort),'demonstration':meta['demonstration'],'results':results,'baselines':baselines,'review':selective,'coverage_error_curve':curve,'evaluated_at':datetime.now(timezone.utc).isoformat()}
    if not known_frame.empty:
        # Remuestreo por grupos; no añade evidencia real a textos elaborados.
        rng=np.random.default_rng(meta['seed'])
        groups=known_frame.grupo_origen.unique()
        scores=[]
        for _ in range(200):
            sample=pd.concat([known_frame[known_frame.grupo_origen.eq(g)] for g in rng.choice(groups,len(groups),replace=True)])
            scores.append(thematic_metrics(model,sample)[0]['macro_f1_present_classes'])
        report['bootstrap_group_macro_f1_95']=[float(x) for x in np.quantile(scores,[.025,.975])]
        report['bootstrap_limit']='200 remuestreos; clases ausentes y pocos grupos limitan interpretación'
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        metrics,_=thematic_metrics(model,known_frame)
        pd.DataFrame(metrics['confusion_matrix'],index=LABELS,columns=LABELS).to_csv(run/f'{partition}_confusion.csv')
        fig,ax=plt.subplots(figsize=(7,6))
        ax.imshow(metrics['confusion_matrix'],cmap='Blues')
        ax.set(xticks=range(8),yticks=range(8),xticklabels=LABELS,yticklabels=LABELS,xlabel='Predicción',ylabel='Referencia',title=f'{partition} · {"elaborados / demo" if meta["demonstration"] else "cohorte independiente"}')
        fig.tight_layout(); fig.savefig(run/f'{partition}_confusion.png'); plt.close(fig)
        fig,ax=plt.subplots()
        ax.plot([r['threshold'] for r in curve],[r['score_only_coverage'] for r in curve],label='Solo puntuación (hipotética)')
        ax.plot([r['threshold'] for r in curve],[r['operational_coverage'] for r in curve],label='Política completa')
        ax.set(xlabel='Umbral',ylabel='Cobertura',ylim=(-.02,1.02)); ax.legend(); fig.tight_layout(); fig.savefig(run/f'{partition}_coverage.png'); plt.close(fig)
    (run/output_name).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    pd.DataFrame(curve).to_csv(run/f'{partition}_coverage.csv',index=False)
    if partition=='test':
        meta['test_evaluated']=True
        (run/'manifest.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    return report

def activate(run,target):
    from ml.inference import Predictor
    run,target=Path(run),Path(target)
    meta=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    if not meta['threshold_version']:
        raise ValueError('Congele el umbral antes de activar')
    if not meta['demonstration'] and not (run/'evaluation.json').exists():
        raise ValueError('Candidato real requiere evaluación independiente antes de activación')
    if Predictor(run/'manifest.json').model is None:
        raise ValueError('Integridad o compatibilidad inválidas')
    target.mkdir(parents=True,exist_ok=True)
    if (target/'active.json').exists():
        archive=target/'archive'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        archive.mkdir(parents=True)
        old=json.loads((target/'active.json').read_text(encoding='utf-8'))
        shutil.copy2(target/'active.json',archive/'manifest.json')
        shutil.copy2(target/old['artifact'],archive/old['artifact'])
    artifact=f'{meta["version"]}.joblib'
    shutil.copy2(run/'pipeline.joblib',target/artifact)
    meta['artifact']=artifact
    temp=target/'active.tmp'
    temp.write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
    temp.replace(target/'active.json')
    return {'active':meta['version'],'restart_api_required':True}
