import json
from backend.main import app
from backend.settings import ROOT
(ROOT/'docs').mkdir(exist_ok=True)
(ROOT/'docs/openapi.json').write_text(json.dumps(app.openapi(),indent=2,ensure_ascii=False),encoding='utf-8')
print('OpenAPI exportado sin arrancar ni entrenar la API')
