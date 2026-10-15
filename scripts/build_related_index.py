"""python -m scripts.build_related_index; nunca invocado por una petición HTTP."""
from backend.db import SessionLocal
from backend.related import build_index
from backend.settings import ROOT

if __name__=='__main__':
    with SessionLocal() as db:
        print(build_index(db,ROOT/'data/private/related_index'))
