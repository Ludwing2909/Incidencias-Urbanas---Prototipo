import os
import tempfile
from pathlib import Path
os.environ['APP_SECRET']='test-secret-only-for-pytest-0123456789abcdef'
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.gettempdir())/'juliaca-pytest.db').replace('\\','/')
os.environ['MODEL_MANIFEST']=str(Path(tempfile.gettempdir())/'missing-academic-model.json')
os.environ['COOKIE_SECURE']='false'
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import Base,engine,SessionLocal,User
from backend.security import hasher

@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for role in ('administrador','revisor'):
            db.add(User(username=role,password_hash=hasher.hash('test-password-123'),role=role))
        db.commit()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def credentials(client,role='administrador'):
    r=client.post('/api/v1/auth/login',json={'usuario':role,'password':'test-password-123'})
    assert r.status_code==200
    return {'X-CSRF-Token':r.json()['csrf_token']}
