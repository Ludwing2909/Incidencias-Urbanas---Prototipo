"""Descarga fuentes públicas solo para inspección; no incorpora filas al entrenamiento."""
import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.request import Request,urlopen
from zoneinfo import ZoneInfo
import pandas as pd
from io import StringIO

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',default='all');parser.add_argument('--max-mib',type=int,default=20);args=parser.parse_args()
    sources=json.loads((ROOT/'config/sources.json').read_text(encoding='utf-8'))
    reports=[]
    raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
    for item in sources:
        if args.source not in ('all',item['id']):continue
        result={**item,'access_date':datetime.now(ZoneInfo('America/Lima')).isoformat(),'rows':None,'columns':None,'training_approved':False}
        try:
            with urlopen(Request(item['url'],headers={'User-Agent':'AcademicSourceInspection/1.0'}),timeout=25) as response:
                content=response.read(args.max_mib*1024*1024+1)
                if len(content)>args.max_mib*1024*1024:raise ValueError(f'Supera límite de inspección de {args.max_mib} MiB')
                result['content_type']=response.headers.get('Content-Type','')
            result['sha256']=hashlib.sha256(content).hexdigest()
            result['bytes']=len(content)
            decoded=None
            for encoding in ('utf-8-sig','cp1252'):
                try:decoded=content.decode(encoding);result['encoding']=encoding;break
                except UnicodeDecodeError:continue
            if decoded is None:raise ValueError('Codificación no reconocida')
            if '<html' in decoded[:2000].lower() or '<!doctype html' in decoded[:2000].lower():
                result['status']='Página HTML; recurso CSV no descargado'
                result['download_candidates']=re.findall(r'(?:https?://[^\s"<>]+\.(?:csv|xlsx)|[^"<>\s]*Reporte_Reclamos_Senace\.csv)',decoded,flags=re.IGNORECASE)[:10]
                (raw/(item['id']+'.html')).write_bytes(content)
            else:
                (raw/(item['id']+'.csv')).write_bytes(content)
                frame=pd.read_csv(StringIO(decoded),sep=None,engine='python',dtype=str,keep_default_na=False)
                result.update(rows=len(frame),columns=frame.columns.tolist(),status='Descargado e inspeccionado; evaluación semántica y permiso pendientes')
                result['nonempty_by_column']={c:int(frame[c].str.strip().ne('').sum()) for c in frame.columns}
                result['unique_by_column']={c:int(frame[c].nunique()) for c in frame.columns}
                # Sin imprimir textos potencialmente personales.
        except Exception as error:
            result['status']='Descarga no completada'
            result['error']=str(error)[:250]
        reports.append(result)
        print(item['id']+': '+result['status'])
    output=ROOT/'reports/source_inspection.json'
    output.parent.mkdir(exist_ok=True)
    if args.source!='all' and output.exists():
        previous=json.loads(output.read_text(encoding='utf-8'))
        reports=[r for r in previous if r['id']!=args.source]+reports
    output.write_text(json.dumps(reports,indent=2,ensure_ascii=False),encoding='utf-8')

if __name__=='__main__':main()
