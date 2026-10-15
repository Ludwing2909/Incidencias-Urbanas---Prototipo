"""Observación de transform en el artefacto ajustado, aislada por petición."""
from copy import copy
from time import perf_counter
from collections import Counter
from sklearn.pipeline import Pipeline

TRACE_VERSION = 'trace-v1'


class ObservedVectorizer:
    def __init__(self, vectorizer, records, member):
        self.vectorizer, self.records, self.member = vectorizer, records, member

    def __getattr__(self, name):
        return getattr(self.vectorizer, name)

    def transform(self, texts):
        started = perf_counter()
        vector = self.vectorizer.transform(texts)
        elapsed = (perf_counter() - started) * 1000
        # Solo inspección después de transform: nunca ajustar al mensaje.
        v = self.vectorizer
        analyzer_started = perf_counter()
        tokens = v.build_analyzer()(texts[0])
        analyzer_ms = (perf_counter() - analyzer_started) * 1000
        counts = Counter(tokens)
        unique = list(dict.fromkeys(tokens))
        names = v.get_feature_names_out()
        row = vector.getrow(0)
        order = sorted(zip(row.indices.tolist(), row.data.tolist()), key=lambda p: (-p[1], names[p[0]]))
        features = [{'termino': str(names[i]), 'peso': float(weight),
                     'frecuencia_analizador': counts[str(names[i])],
                     'idf': float(v.idf_[i]) if v.use_idf else None} for i, weight in order[:30]]
        params = {k: v.get_params()[k] for k in ('analyzer', 'ngram_range', 'lowercase', 'strip_accents', 'stop_words', 'norm', 'use_idf', 'smooth_idf', 'sublinear_tf', 'binary', 'token_pattern')}
        params['preprocessor'] = getattr(v.preprocessor, '__name__', None)
        self.records.append({'miembro': self.member, 'tiempo_ms': round(elapsed, 4), 'analizador_ms': round(analyzer_ms,4),
            'parametros': params, 'vocabulario_tamano': len(v.vocabulary_),
            'caracteristicas_total': len(tokens), 'caracteristicas_unicas': len(unique),
            'caracteristicas': [{'termino': t, 'en_vocabulario': t in v.vocabulary_,
                'tipo': 'caracteres' if str(v.analyzer).startswith('char') else ('bigrama' if len(t.split()) == 2 else 'palabra' if len(t.split()) == 1 else 'ngrama')} for t in unique[:80]],
            'caracteristicas_truncadas': len(unique) > 80,
            'no_nulas': row.nnz, 'pesos': features, 'pesos_truncados': row.nnz > 30,
            'vector_vacio': row.nnz == 0})
        return vector


def observed_pipeline(pipeline, records, member):
    if not isinstance(pipeline, Pipeline) or 'tfidf' not in pipeline.named_steps:
        return pipeline
    local = copy(pipeline)
    local.steps = [(name, ObservedVectorizer(step, records, member) if name == 'tfidf' else step)
                   for name, step in pipeline.steps]
    return local


def observe_model(model, records):
    local = copy(model)
    if hasattr(model, 'calibrated_classifiers_'):
        local.calibrated_classifiers_ = []
        for i, member in enumerate(model.calibrated_classifiers_):
            observed = copy(member)
            observed.estimator = observed_pipeline(member.estimator, records, i + 1)
            local.calibrated_classifiers_.append(observed)
        return local
    return observed_pipeline(model, records, 1)


def model_description(model):
    if model is None:
        return {'disponible': False}
    calibrated = hasattr(model, 'calibrated_classifiers_')
    members = [m.estimator for m in model.calibrated_classifiers_] if calibrated else [model]
    estimator = members[0].steps[-1][1] if isinstance(members[0], Pipeline) else members[0]
    params = estimator.get_params()
    representation=[]
    for member in members:
        if isinstance(member,Pipeline) and 'tfidf' in member.named_steps:
            vectorizer=member.named_steps['tfidf']
            representation.append({**{k:vectorizer.get_params()[k] for k in ('analyzer','ngram_range','norm','use_idf','smooth_idf','sublinear_tf','binary','lowercase','strip_accents','stop_words','token_pattern')},
                'preprocessor':getattr(vectorizer.preprocessor,'__name__',None),
                'nota_preprocesador':'Un preprocesador callable sustituye el preprocesado predeterminado; consulte las características observadas para ver mayúsculas y tildes efectivas.'})
    return {'disponible': True, 'envoltura': type(model).__name__,
        'estimador': type(estimator).__name__,
        'parametros': {k: params[k] for k in ('C', 'kernel', 'class_weight', 'alpha', 'loss') if k in params},
        'calibracion': getattr(model, 'method', None) if calibrated else None,
        'miembros': len(members), 'representacion':representation,
        'metodo_base': 'decision_function' if hasattr(estimator, 'decision_function') else 'predict_proba' if hasattr(estimator, 'predict_proba') else 'predict',
        'metodo_salida': 'predict_proba' if hasattr(model, 'predict_proba') else 'decision_function',
        'limite': 'Pesos TF-IDF no son contribuciones causales. No se calculan atribuciones por coeficientes.'}
