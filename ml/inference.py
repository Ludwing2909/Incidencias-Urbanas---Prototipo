import hashlib
import importlib.metadata
import json
from pathlib import Path
import joblib
from ml.text import anonymize

LABELS = [f'C{i}' for i in range(1, 9)]

class Predictor:
    def __init__(self, manifest_path):
        self.model = None
        self.manifest = {}
        self.error = 'modelo no disponible'
        try:
            path = Path(manifest_path).resolve()
            meta = json.loads(path.read_text(encoding='utf-8'))
            artifact = (path.parent / meta['artifact']).resolve()
            if artifact.parent != path.parent or meta['labels'] != LABELS:
                raise ValueError('Contrato del modelo inválido')
            for dependency in ('scikit-learn', 'numpy', 'joblib'):
                if importlib.metadata.version(dependency) != meta['dependencies'][dependency]:
                    raise ValueError('Dependencias incompatibles')
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != meta['sha256']:
                raise ValueError('Integridad del modelo inválida')
            # Ruta administrativa local. Nunca aceptar archivos desde HTTP.
            model = joblib.load(artifact)
            if sorted(model.classes_.tolist()) != LABELS:
                raise ValueError('Clases incompatibles')
            self.model, self.manifest, self.error = model, meta, None
        except Exception:
            self.error = 'modelo no disponible o incompatible'

    def predict(self, text):
        return self.execute(text)[0]

    def execute(self, text, traced=False):
        """La misma ejecución sirve a la API, al registro y a la traza."""
        from ml.trace import observe_model
        records = []
        if self.model is None:
            return (None, None, None), records
        text = anonymize(text)
        model = observe_model(self.model, records) if traced else self.model
        if hasattr(model, 'predict_proba'):
            p = model.predict_proba([text])[0]
            idx = int(p.argmax())
            kind = 'probabilidad_calibrada' if hasattr(model, 'calibrated_classifiers_') else 'probabilidad'
            return (str(model.classes_[idx]), float(p[idx]), kind), records
        topic = str(model.predict([text])[0])
        margin = float(model.decision_function([text])[0].max())
        return (topic, margin, 'margen'), records
