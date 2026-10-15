import os
import subprocess
import sys
from pathlib import Path
from sqlalchemy import create_engine,inspect

def test_migration_upgrade_downgrade_upgrade(tmp_path):
    path=tmp_path/'migrated.db';env={**os.environ,'DATABASE_URL':'sqlite:///'+str(path).replace('\\','/')}
    for revision in ('upgrade','downgrade','upgrade'):
        command=[sys.executable,'-m','alembic',revision,'base' if revision=='downgrade' else 'head']
        result=subprocess.run(command,env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    tables=set(inspect(create_engine(env['DATABASE_URL'])).get_table_names())
    assert {'incidents','predictions','reviews','audit','year_sequences','sessions','model_versions','rules'}<=tables
