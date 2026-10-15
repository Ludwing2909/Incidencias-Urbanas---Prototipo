"""Servicio transaccional de registro, independiente de la capa HTTP."""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from backend.db import Incident,Prediction,StateHistory,YearSequence,Audit
from backend.security import digest
from backend.services import classify
from ml.text import anonymize

class RegistrationConflict(Exception):
    """La clave ya representa otro cuerpo o hubo conflicto transaccional."""

def payload(db,row,secret):
    pred=db.scalar(select(Prediction).where(Prediction.incident_id==row.id))
    return {'id':row.id,'codigo':row.code,'secreto_seguimiento':secret,'clasificacion':pred.result}

def record_incident(db,predictor,body,idempotency_key):
    key_hash=digest(idempotency_key)
    request_hash=digest(body.model_dump_json())
    tracking_secret=digest('tracking:'+idempotency_key)
    existing=db.scalar(select(Incident).where(Incident.idempotency_hash==key_hash))
    if existing:
        if existing.request_hash!=request_hash:
            raise RegistrationConflict('Clave de reintento utilizada con otra descripción')
        return payload(db,existing,tracking_secret),False
    year=datetime.now(ZoneInfo('America/Lima')).year
    insert=sqlite_insert if db.bind.dialect.name=='sqlite' else pg_insert
    sequence=db.execute(insert(YearSequence).values(year=year,value=1).on_conflict_do_update(index_elements=['year'],set_={'value':YearSequence.value+1}).returning(YearSequence.value)).scalar_one()
    clean_text=anonymize(body.descripcion)
    result,latency=classify(db,predictor,clean_text,body.ubicacion_general)
    row=Incident(code=f'REC-{year}-{sequence:05d}',year=year,sequence=sequence,secret_hash=digest(tracking_secret),idempotency_hash=key_hash,request_hash=request_hash,text=clean_text,location=anonymize(body.ubicacion_general) if body.ubicacion_general else None,state=result['estado'],current_topic=result['tema'],current_destination=result['destino_sugerido'])
    db.add(row)
    try:
        db.flush()
        db.add(Prediction(incident_id=row.id,result=result,latency_ms=latency))
        db.add(StateHistory(incident_id=row.id,state=row.state,reason='Registro académico; no implica recepción municipal'))
        db.add(Audit(user_id=None,action='registro',entity_id=row.id,changes={'state':row.state}))
        db.commit()
    except IntegrityError:
        db.rollback()
        existing=db.scalar(select(Incident).where(Incident.idempotency_hash==key_hash))
        if existing and existing.request_hash==request_hash:
            return payload(db,existing,tracking_secret),False
        raise RegistrationConflict('Conflicto de registro; reintente') from None
    return {'id':row.id,'codigo':row.code,'secreto_seguimiento':tracking_secret,'clasificacion':result},True
