"""Verificación aislada de PostgreSQL, sin tocar la base de demostración.

python -m scripts.verify_postgres
Requiere Docker Linux operativo. Conserva resultado, no credenciales operativas.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]

def main():
    report={'fecha':datetime.now(timezone.utc).isoformat(),'estado':'no ejecutado','comprobaciones':[]}
    target=ROOT/'reports/postgres_verificacion.json'
    def run(args,**kwargs):
        return subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=kwargs.pop('timeout',120),**kwargs)
    project='pln-verify-'+uuid4().hex[:10]
    compose=['docker','compose','-p',project,'-f','compose.verificacion.yaml']
    started=False
    try:
        engine=run(['docker','info','--format','{{.ServerVersion}}'],timeout=20)
        if engine.returncode:
            report.update(estado='bloqueado',motivo='Motor Docker Linux no disponible; migraciones, concurrencia y restauración PostgreSQL no ejecutadas')
            return
        started=True
        up=run(compose+['up','-d','--wait'],timeout=180)
        if up.returncode:raise RuntimeError('No se inició el entorno aislado PostgreSQL')
        endpoint=run(compose+['port','db','5432']).stdout.strip()
        port=int(endpoint.rsplit(':',1)[1])
        url=f'postgresql+psycopg://pln_test:local-test-only-123456789@127.0.0.1:{port}/pln_test'
        os.environ['DATABASE_URL']=url
        os.environ['APP_SECRET']='isolated-postgres-test-only-0123456789abcdef'
        os.environ['MODEL_MANIFEST']=str(ROOT/'tests/no-model.json')
        from alembic.config import Config
        from alembic import command
        from backend.db import SessionLocal,engine as db_engine,Incident
        from backend.registration import record_incident
        from backend.schemas import IncidentInput
        from ml.inference import Predictor
        from sqlalchemy import func,select
        config=Config(str(ROOT/'alembic.ini'))
        for action in ('upgrade','downgrade','upgrade'):
            getattr(command,action)(config,'base' if action=='downgrade' else 'head')
        report['comprobaciones'].append('upgrade/downgrade/upgrade 0002')
        predictor=Predictor(ROOT/'tests/no-model.json')
        def register(key):
            with SessionLocal() as db:
                return record_incident(db,predictor,IncidentInput(descripcion='Hay basura en una vía de prueba.'),key)[0]['codigo']
        with ThreadPoolExecutor(max_workers=6) as pool:
            codes=list(pool.map(register,[str(uuid4()) for _ in range(12)]))
        assert len(set(codes))==12
        shared=str(uuid4())
        with ThreadPoolExecutor(max_workers=4) as pool:
            repeats=list(pool.map(register,[shared]*4))
        assert len(set(repeats))==1
        db_engine.dispose()
        with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(Incident))==13
        report['comprobaciones']+=['12 registros concurrentes únicos','4 reintentos idempotentes','persistencia tras reconexión']
        for args in [['exec','-T','db','pg_dump','-U','pln_test','-d','pln_test','-Fc','-f','/tmp/pln.dump'],
                     ['exec','-T','db','createdb','-U','pln_test','pln_restore'],
                     ['exec','-T','db','pg_restore','-U','pln_test','-d','pln_restore','--no-owner','/tmp/pln.dump']]:
            assert run(compose+args).returncode==0
        count=run(compose+['exec','-T','db','psql','-U','pln_test','-d','pln_restore','-Atc','SELECT count(*) FROM incidents']).stdout.strip()
        assert count=='13'
        report['comprobaciones']+=['pg_dump custom','pg_restore en base vacía aislada','13 casos restaurados']
        report.update(estado='pasado',limite='Verifica persistencia PostgreSQL aislada; no acredita despliegue institucional ni stack completo frontend/API Docker')
    except (OSError,subprocess.SubprocessError,RuntimeError,AssertionError,ValueError) as exc:
        report.update(estado='fallido',motivo=type(exc).__name__+' durante la verificación aislada')
    finally:
        if started:
            run(compose+['down'])  # Solo este proyecto de prueba aleatorio; sin volúmenes persistentes.
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2))
    return report['estado']

if __name__=='__main__':main()
