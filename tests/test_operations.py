import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import nbformat

ROOT=Path(__file__).resolve().parents[1]

def test_sqlite_backup_integrity(tmp_path):
    source,target=tmp_path/'original.db',tmp_path/'backup.db'
    with sqlite3.connect(source) as db:
        db.execute('CREATE TABLE fixture (id INTEGER PRIMARY KEY, value TEXT)')
        db.execute('INSERT INTO fixture VALUES (1,?)',('Texto elaborado sin identificadores',))
    result=subprocess.run([sys.executable,'-m','scripts.sqlite_backup',str(source),str(target)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    with sqlite3.connect(target) as db:
        assert db.execute('SELECT value FROM fixture').fetchone()[0]=='Texto elaborado sin identificadores'
    repeat=subprocess.run([sys.executable,'-m','scripts.sqlite_backup',str(source),str(target)],capture_output=True,text=True)
    assert repeat.returncode==2

def test_notebooks_valid_and_compile():
    for path in (ROOT/'notebooks').glob('*.ipynb'):
        notebook=nbformat.read(path,as_version=4)
        nbformat.validate(notebook)
        for cell in notebook.cells:
            if cell.cell_type=='code':compile(cell.source,str(path),'exec')
        assert not any(cell.get('outputs') for cell in notebook.cells)
