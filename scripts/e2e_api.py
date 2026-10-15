"""Servidor aislado de integración: credenciales exclusivamente de pruebas."""
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
os.environ['APP_SECRET']='test-only-secret-for-integration-0123456789'
os.environ['DATABASE_URL']='sqlite:///'+str(ROOT/'tests/e2e.db').replace('\\','/')
os.environ['MODEL_MANIFEST']=str(ROOT/'models/active.json' if (ROOT/'models/active.json').exists() else ROOT/'tests/no-model.json')
os.environ['COOKIE_SECURE']='false'
from alembic.config import Config
from alembic import command
from backend.db import SessionLocal,User,RateBucket
from backend.security import hasher
from sqlalchemy import select,delete
command.upgrade(Config(str(ROOT/'alembic.ini')),'head')
with SessionLocal() as db:
    # Solo la base aislada tests/e2e.db: cada suite empieza sin límites de suites previas.
    db.execute(delete(RateBucket))
    if not db.scalar(select(User).where(User.username=='test-admin')):
        db.add(User(username='test-admin',password_hash=hasher.hash('Test-password-123!'),role='administrador'))
    db.commit()
import uvicorn
uvicorn.run('backend.main:app',host='127.0.0.1',port=8000,access_log=False)
