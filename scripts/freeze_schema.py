"""Solo para confeccionar la migración inicial. No ejecutar tras cambiar modelos."""
import json
from backend.db import Base
from backend.settings import ROOT
spec=[]
for table in Base.metadata.sorted_tables:
    columns=[]
    for c in table.columns:
        columns.append({'name':c.name,'type':type(c.type).__name__,'length':getattr(c.type,'length',None),'pk':c.primary_key,'nullable':c.nullable,'foreign_key':next((f.target_fullname for f in c.foreign_keys),None)})
    unique=[list(c.columns.keys()) for c in table.constraints if type(c).__name__=='UniqueConstraint']
    spec.append({'name':table.name,'columns':columns,'unique':unique})
path=ROOT/'backend/migrations/schema_v1.json'
if path.exists():raise SystemExit('Snapshot ya existe; no modificar una migración aplicada')
path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
