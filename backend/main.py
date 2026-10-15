import hashlib
import hmac
import json
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, update, func, delete, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from backend import settings
from backend.db import get_db, SessionLocal, Incident, Prediction, Review, StateHistory, Rule, Audit, User, LoginSession, YearSequence, ModelVersion, now
from backend.schemas import IncidentInput, FollowInput, LoginInput, ReviewInput, TransitionInput, RuleInput, Registration
from backend.schemas import FollowResult, IncidentPage, IncidentDetail, RuleResult, StateResult, LoginResult, StatsResult, ModelResult
from backend.security import digest, verify_password, DUMMY_HASH, staff, admin, create_session, limit
from backend.services import CATEGORIES, classify
from ml.inference import Predictor
from ml.text import anonymize
from backend.registration import record_incident, RegistrationConflict

@asynccontextmanager
async def lifespan(app):
    if len(settings.APP_SECRET) < 32:
        raise RuntimeError('Configure APP_SECRET con al menos 32 caracteres aleatorios')
    app.state.predictor = Predictor(settings.MODEL_MANIFEST)
    if app.state.predictor.model is not None:
        with SessionLocal() as db:
            meta = app.state.predictor.manifest
            if not db.get(ModelVersion, meta['version']):
                db.add(ModelVersion(id=meta['version'], manifest=meta))
                db.commit()
    yield

app = FastAPI(title='Incidencias urbanas de Juliaca · Prototipo académico', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True,
    allow_methods=['GET','POST','PATCH'], allow_headers=['Content-Type','X-CSRF-Token','Idempotency-Key'])
from backend.pln_routes import router as pln_router
app.include_router(pln_router)

@app.middleware('http')
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    return JSONResponse(status_code=503, content={'detail':'Persistencia no disponible; puede reintentar con la misma clave'})

def audit(db, user, action, entity_id, changes):
    db.add(Audit(user_id=user.id if user else None, action=action, entity_id=entity_id, changes=changes))

def incident_or_404(db, id):
    row = db.get(Incident, id)
    if row is None:
        raise HTTPException(404, 'Incidencia no encontrada')
    return row

def serial(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}

def summary(row):
    return {k:v for k,v in serial(row).items() if k not in ('secret_hash','idempotency_hash','request_hash','text','location')}

def claim_revision(db, row, version, values):
    changed = db.execute(update(Incident).where(Incident.id == row.id, Incident.revision == version).values(**values, revision=version+1).execution_options(synchronize_session=False)).rowcount
    if not changed:
        db.rollback()
        raise HTTPException(409, 'El caso cambió; recargue antes de revisar')

@app.get('/api/v1/health/live')
def live():
    return {'status':'live'}

@app.get('/api/v1/health/ready')
def ready(request: Request, db=Depends(get_db)):
    db.execute(text('SELECT 1'))
    # Sin modelo la API sigue lista para registrar; degradación explícita.
    db.execute(select(YearSequence).limit(1))
    return {'status':'ready', 'modelo_disponible':request.app.state.predictor.model is not None}

@app.get('/api/v1/categorias')
def categories():
    return {'version':'C1-C8-v1','categorias':CATEGORIES,'R9':'Ruta de revisión humana; no es clase ni oficina'}

@app.post('/api/v1/incidencias', response_model=Registration, status_code=201)
def register(body: IncidentInput, request: Request, response: Response,
        idempotency_key: str = Header(alias='Idempotency-Key', min_length=32, max_length=100), db=Depends(get_db)):
    limit(db, request, 'register', 40)
    try:
        result,created=record_incident(db,request.app.state.predictor,body,idempotency_key)
    except RegistrationConflict as error:
        raise HTTPException(409,str(error)) from None
    response.status_code=201 if created else 200
    return result

@app.post('/api/v1/seguimiento/consulta', response_model=FollowResult)
def follow(body: FollowInput, request: Request, db=Depends(get_db)):
    limit(db, request, 'follow', 15)
    row = db.scalar(select(Incident).where(Incident.code == body.codigo.upper().strip()))
    expected = row.secret_hash if row else digest('nonexistent-secret')
    if not hmac.compare_digest(expected, digest(body.secreto)) or row is None:
        raise HTTPException(404, 'Código o secreto de consulta inválidos')
    history = db.scalars(select(StateHistory).where(StateHistory.incident_id == row.id).order_by(StateHistory.created_at))
    return {'codigo':row.code,'estado':row.state,'fecha':row.created_at,'cronologia':[{'estado':h.state,'fecha':h.created_at} for h in history]}

@app.post('/api/v1/auth/login', response_model=LoginResult)
def login(body: LoginInput, request: Request, response: Response, db=Depends(get_db)):
    limit(db, request, 'login', 10)
    user = db.scalar(select(User).where(User.username == body.usuario))
    valid = verify_password(user.password_hash if user else DUMMY_HASH, body.password)
    if not valid or user is None:
        raise HTTPException(401, 'Credenciales inválidas')
    token, csrf = create_session(db, user)
    response.set_cookie('session', token, httponly=True, secure=settings.COOKIE_SECURE, samesite='strict', max_age=28800, path='/api')
    return {'usuario':user.username,'rol':user.role,'csrf_token':csrf}

@app.get('/api/v1/auth/me')
def me(user=Depends(staff)):
    return {'usuario':user.username,'rol':user.role}

@app.post('/api/v1/auth/logout', status_code=204)
def logout(request: Request, response: Response, user=Depends(staff), db=Depends(get_db)):
    db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(request.cookies.get('session',''))))
    db.commit()
    response.delete_cookie('session',path='/api')

@app.get('/api/v1/admin/incidencias', response_model=IncidentPage)
def inbox(q: str = Query('',max_length=100), categoria: str | None=None, estado: str | None=None,
        page: int=Query(1,ge=1), size: int=Query(20,ge=1,le=100), user=Depends(staff), db=Depends(get_db)):
    stmt = select(Incident)
    if q:
        safe = q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        stmt = stmt.where(Incident.code.ilike(f'%{safe}%', escape='\\'))
    if categoria:
        stmt = stmt.where(Incident.current_topic == categoria)
    if estado:
        stmt = stmt.where(Incident.state == estado)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Incident.created_at.desc()).offset((page-1)*size).limit(size))
    return {'items':[summary(r) for r in rows],'total':total,'page':page,'size':size}

@app.get('/api/v1/admin/incidencias/{id}', response_model=IncidentDetail)
def detail(id: str, user=Depends(staff), db=Depends(get_db)):
    row = incident_or_404(db,id)
    pred = db.scalar(select(Prediction).where(Prediction.incident_id == id))
    return {**summary(row),'texto':row.text,'ubicacion_general':row.location,'prediccion':pred.result,
        'latencia_ms':pred.latency_ms,
        'revisiones':[serial(r) for r in db.scalars(select(Review).where(Review.incident_id == id).order_by(Review.created_at))],
        'historial':[serial(h) for h in db.scalars(select(StateHistory).where(StateHistory.incident_id == id).order_by(StateHistory.created_at))]}

@app.post('/api/v1/admin/incidencias/{id}/revision', response_model=StateResult)
def review(id: str, body: ReviewInput, user=Depends(staff), db=Depends(get_db)):
    row = incident_or_404(db,id)
    if row.state in ('Derivado','Resuelto'):
        raise HTTPException(409,'Reabra el caso antes de corregirlo')
    old_topic, old_destination, old_state = row.current_topic, row.current_destination, row.state
    claim_revision(db,row,body.version,{'current_topic':body.tema,'current_destination':body.destino,'state':'Revisado'})
    db.add(Review(incident_id=id,user_id=user.id,original_topic=old_topic,topic=body.tema,original_destination=old_destination,destination=body.destino,reason=body.motivo))
    db.add(StateHistory(incident_id=id,user_id=user.id,previous=old_state,state='Revisado',reason=body.motivo))
    audit(db,user,'revision',id,{'tema_original':old_topic,'tema_corregido':body.tema,'destino_original':old_destination,'destino_corregido':body.destino})
    db.commit()
    return {'estado':'Revisado','version':body.version+1}

@app.post('/api/v1/admin/incidencias/{id}/transiciones', response_model=StateResult)
def transition(id: str, body: TransitionInput, user=Depends(staff), db=Depends(get_db)):
    row = incident_or_404(db,id)
    allowed = {'Pendiente de revisión':set(),'Sugerencia disponible':{'Pendiente de revisión'},'Revisado':{'Pendiente de revisión','Derivado'},'Derivado':{'Pendiente de revisión','Resuelto'},'Resuelto':{'Pendiente de revisión'}}
    if body.estado not in allowed.get(row.state,set()):
        raise HTTPException(409,'Transición no permitida; use revisión para confirmar el caso')
    if body.estado in ('Derivado','Resuelto'):
        if user.role != 'administrador':
            raise HTTPException(403,'Solo un administrador confirma actuaciones oficiales')
        if not body.confirmacion_humana or not body.evidencia or len(body.evidencia.strip()) < 8:
            raise HTTPException(422,'Se requiere confirmación humana y evidencia de actuación')
        if not row.current_topic or not row.current_destination:
            raise HTTPException(422,'Confirme tema y destino antes de derivar')
    previous = row.state
    claim_revision(db,row,body.version,{'state':body.estado})
    db.add(StateHistory(incident_id=id,user_id=user.id,previous=previous,state=body.estado,reason=body.motivo,evidence=body.evidencia))
    audit(db,user,'transicion',id,{'anterior':previous,'estado':body.estado})
    db.commit()
    return {'estado':body.estado,'version':body.version+1}

@app.get('/api/v1/admin/reglas', response_model=list[RuleResult])
def rules(user=Depends(staff), db=Depends(get_db)):
    return [serial(r) for r in db.scalars(select(Rule).order_by(Rule.category, Rule.version.desc()))]

@app.post('/api/v1/admin/reglas',status_code=201,response_model=RuleResult)
def create_rule(body: RuleInput, user=Depends(admin), db=Depends(get_db)):
    row = Rule(**body.model_dump(mode='json', exclude={'version'}),version=1)
    db.add(row)
    db.flush()
    audit(db,user,'crear_regla',row.id,serial(row))
    db.commit()
    return serial(row)

@app.patch('/api/v1/admin/reglas/{id}',response_model=RuleResult)
def patch_rule(id: str, body: RuleInput, user=Depends(admin), db=Depends(get_db)):
    old = db.get(Rule,id)
    if not old or not old.active:
        raise HTTPException(404,'Regla activa no encontrada')
    if body.version != old.version:
        raise HTTPException(409,'Versión de regla desactualizada')
    changed = db.execute(update(Rule).where(Rule.id == id, Rule.active == True, Rule.version == body.version).values(active=False).execution_options(synchronize_session=False)).rowcount
    if not changed:
        db.rollback()
        raise HTTPException(409,'La regla cambió; recargue')
    row = Rule(**body.model_dump(mode='json', exclude={'version'}),version=old.version+1)
    db.add(row)
    db.flush()
    audit(db,user,'versionar_regla',row.id,{'anterior':id,'version':row.version,'regla':serial(row)})
    db.commit()
    return serial(row)

@app.get('/api/v1/admin/estadisticas',response_model=StatsResult)
def statistics(user=Depends(staff), db=Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Incident))
    by_category = dict(db.execute(select(Incident.current_topic,func.count()).group_by(Incident.current_topic)).all())
    by_state = dict(db.execute(select(Incident.state,func.count()).group_by(Incident.state)).all())
    predictions = db.scalars(select(Prediction)).all()
    reviews = db.scalars(select(Review)).all()
    reasons = {}
    original_corrections = {**{c:0 for c in CATEGORIES},'SIN_TEMA':0}
    reviewed_ids = {r.incident_id for r in reviews}
    for p in predictions:
        for reason in p.result['motivos_revision']:
            reasons[reason] = reasons.get(reason,0)+1
        if p.incident_id in reviewed_ids:
            row=db.get(Incident,p.incident_id)
            if row.current_topic != p.result['tema']:
                key=p.result['tema'] or 'SIN_TEMA'
                original_corrections[key]=original_corrections.get(key,0)+1
    return {'total':total,'por_categoria':{c:by_category.get(c,0) for c in CATEGORIES},'sin_tema':by_category.get(None,0),
        'por_estado':by_state,'motivos_revision':reasons,'revisados':len({r.incident_id for r in reviews}),
        'correcciones':sum(r.original_topic != r.topic or r.original_destination != r.destination for r in reviews),
        'latencia_media_ms':sum(p.latency_ms for p in predictions)/len(predictions) if predictions else None,
        'tasa_revision_inicial':sum(p.result['requiere_revision'] for p in predictions)/len(predictions) if predictions else None,
        'correcciones_por_categoria':original_corrections}

@app.get('/api/v1/admin/modelo',response_model=ModelResult)
def model(request: Request,user=Depends(staff)):
    p = request.app.state.predictor
    return {'disponible':p.model is not None,'motivo':p.error,'manifiesto':p.manifest,
        'limites':['No determina veracidad','C7 y C8 requieren revisión de competencia','Sin evaluación real no acredita rendimiento en Juliaca']}

@app.get('/api/v1/admin/experimentos')
def experiments(user=Depends(staff)):
    files = sorted((settings.ROOT / 'reports').glob('runs/*/experiment.json'))
    return [json.loads(p.read_text(encoding='utf-8')) for p in files[-20:]]

@app.get('/api/v1/admin/fuentes')
def sources(user=Depends(staff)):
    # Solo reportes agregados locales: nunca archivos originales ni coordenadas.
    files=sorted((settings.ROOT/'reports/sources').glob('*.json'))
    return [json.loads(p.read_text(encoding='utf-8')) for p in files]
