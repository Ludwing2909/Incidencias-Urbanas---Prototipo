import argparse
import sqlite3
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('target');a=p.parse_args()
    source,target=Path(a.source).resolve(),Path(a.target).resolve()
    if not source.exists() or source==target or target.exists():
        p.exit(2,'Origen no existente o destino no nuevo\n')
    target.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as original,sqlite3.connect(target) as backup:
        original.backup(backup)
        result=backup.execute('PRAGMA integrity_check').fetchone()[0]
        if result!='ok':raise RuntimeError('Respaldo no íntegro')
    print('Copia SQLite íntegra; mantenga acceso restringido')

if __name__=='__main__':main()
