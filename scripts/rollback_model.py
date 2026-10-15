import argparse
import json
import shutil
from pathlib import Path
from ml.inference import Predictor

def main():
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--target',default='models');a=p.parse_args()
    archive,target=Path(a.archive),Path(a.target)
    predictor=Predictor(archive/'manifest.json')
    if predictor.model is None:p.exit(2,'Archivo no confiable, incompatible o faltante\n')
    meta=predictor.manifest
    # La versión activa actual se conserva como un candidato de rollback.
    if (target/'active.json').exists():
        from datetime import datetime,timezone
        preserved=target/'archive'/('before-rollback-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
        preserved.mkdir(parents=True)
        current=json.loads((target/'active.json').read_text(encoding='utf-8'))
        shutil.copy2(target/'active.json',preserved/'manifest.json')
        shutil.copy2(target/current['artifact'],preserved/current['artifact'])
    shutil.copy2(archive/meta['artifact'],target/meta['artifact'])
    temp=target/'rollback.tmp';temp.write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8');temp.replace(target/'active.json')
    print('Rollback completado; reinicie API')

if __name__=='__main__':main()
