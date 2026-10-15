from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.db import get_db, Incident, AnalysisVersion, RelationDecision, Audit
from backend.schemas import AnalysisInput, AnalysisResult, ClarificationInput, RelationInput, ExtractionCorrectionInput
from backend.security import staff, limit
from backend.settings import ROOT
from backend.pln import analyze
from backend.pln_metadata import public_metadata, experimental_audit, capabilities
from backend.related import search_related
from ml.text import anonymize
from ml.inference import Predictor

router=APIRouter()

def get_incident(db,id):
    row=db.get(Incident,id)
    if row is None:
        raise HTTPException(404,'Incidencia no encontrada')
    return row

def latest(db,id):
    return db.scalar(select(AnalysisVersion).where(AnalysisVersion.incident_id==id).order_by(AnalysisVersion.version.desc()).limit(1))

def view(row):
    return {'version':row.version,'original':row.original_text,'respuestas':row.answers,'analisis':row.analysis,'fecha':row.created_at}

def corrected_extraction(result,answers):
    for key,value in answers.items():
        if key.startswith('extraccion:'):
            field=key.split(':',1)[1]
            result['extraccion']['campos'][field]={'valor':value,'evidencia':value,'origen':'corrección humana (respuesta del personal)'}
    return result

def save_analysis(db,user,incident,version,original,answers,result):
    row=AnalysisVersion(incident_id=incident.id,user_id=user.id,version=version,original_text=original,
        answers=answers,analysis=AnalysisResult.model_validate(result).model_dump(mode='json'))
    db.add(row)
    db.add(Audit(user_id=user.id,action='analisis_pln',entity_id=incident.id,changes={'version_analisis':version}))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'El análisis cambió; recargue antes de responder') from None
    return view(row)

@router.post('/api/v1/pln/analizar',response_model=AnalysisResult)
def analysis(body:AnalysisInput,request:Request,db=Depends(get_db)):
    limit(db,request,'pln-analysis',30)
    return analyze(db,request.app.state.predictor,body.descripcion,body.ubicacion_general)

@router.get('/api/v1/pln/metadatos')
def metadata(request:Request):
    return public_metadata(request.app.state.predictor)

@router.get('/api/v1/pln/capacidades')
def roadmap():
    return capabilities()

@router.get('/api/v1/admin/pln/datos')
def data_audit(request:Request,version:str | None=Query(None,pattern=r'^[a-zA-Z0-9_-]{1,100}$'),user=Depends(staff)):
    predictor=request.app.state.predictor
    if version:
        base=(ROOT/'reports/runs').resolve()
        run=(base/version).resolve()
        if run.parent!=base or not (run/'manifest.json').is_file():
            raise HTTPException(404,'Experimento no disponible')
        candidate=Predictor(run/'manifest.json')
        if candidate.model is None:
            raise HTTPException(404,'Artefacto del experimento no disponible o incompatible')
        predictor=candidate
    return experimental_audit(predictor)

@router.get('/api/v1/admin/incidencias/{id}/analisis')
def analysis_history(id:str,user=Depends(staff),db=Depends(get_db)):
    get_incident(db,id)
    return [view(r) for r in db.scalars(select(AnalysisVersion).where(AnalysisVersion.incident_id==id).order_by(AnalysisVersion.version.desc()).limit(50))]

@router.post('/api/v1/admin/incidencias/{id}/analisis')
def stored_analysis(id:str,request:Request,user=Depends(staff),db=Depends(get_db)):
    row=get_incident(db,id)
    previous=latest(db,id)
    if previous:
        return view(previous)
    original=anonymize(row.text)
    return save_analysis(db,user,row,1,original,{},analyze(db,request.app.state.predictor,original,row.location))

@router.post('/api/v1/admin/incidencias/{id}/aclaraciones')
def clarify(id:str,body:ClarificationInput,request:Request,user=Depends(staff),db=Depends(get_db)):
    incident=get_incident(db,id)
    previous=latest(db,id)
    if not previous or previous.version!=body.version:
        raise HTTPException(409,'El análisis cambió; recargue antes de responder')
    pending={p['id'] for p in previous.analysis['preguntas']}
    if not set(body.respuestas).issubset(pending):
        raise HTTPException(422,'Solo se admiten respuestas a preguntas pendientes')
    answers={**previous.answers,**{k:anonymize(v) for k,v in body.respuestas.items()}}
    labels={'problema_principal':'Problema principal','lugar_general':'Lugar general','referencia_temporal':'Referencia temporal','tema_principal':'Problema a priorizar'}
    combined=previous.original_text+'\n'+'\n'.join(f'{labels[k]}: {v}' for k,v in answers.items() if k in labels)
    if len(combined)>3000:
        raise HTTPException(422,'El texto y las respuestas superan el límite de 3000 caracteres')
    result=analyze(db,request.app.state.predictor,combined,incident.location,answers)
    for key in ('problema_principal','lugar_general','referencia_temporal'):
        if key in answers:
            result['extraccion']['campos'][key]={'valor':answers[key],'evidencia':answers[key],'origen':'respuesta humana'}
    return save_analysis(db,user,incident,body.version+1,previous.original_text,answers,corrected_extraction(result,answers))

@router.post('/api/v1/admin/incidencias/{id}/extraccion')
def correct_fields(id:str,body:ExtractionCorrectionInput,user=Depends(staff),db=Depends(get_db)):
    incident=get_incident(db,id)
    previous=latest(db,id)
    if not previous or previous.version!=body.version:
        raise HTTPException(409,'El análisis cambió; recargue antes de corregir')
    answers={**previous.answers,**{'extraccion:'+k:anonymize(v) if v is not None else None for k,v in body.campos.items()}}
    # La corrección de un campo no vuelve a clasificar ni cambia su predicción.
    import copy
    result=corrected_extraction(copy.deepcopy(previous.analysis),answers)
    for stage in result['etapas']:
        if stage['id']=='extraccion':
            stage['salida']=result['extraccion']
            stage['transformaciones']=[*stage['transformaciones'],'Corrección humana guardada por separado; no vuelve a inferir']
    return save_analysis(db,user,incident,body.version+1,previous.original_text,answers,result)

@router.get('/api/v1/admin/incidencias/{id}/relacionados')
def related(id:str,top_k:int=Query(5,ge=1,le=10),umbral:float=Query(.25,ge=0,le=1),user=Depends(staff),db=Depends(get_db)):
    row=get_incident(db,id)
    result=search_related(db,row,ROOT/'data/private/related_index',top_k,umbral)
    result['decisiones']=[{'relacionado_id':r.related_id,'decision':r.decision,'motivo':r.reason,'fecha':r.created_at} for r in db.scalars(select(RelationDecision).where(RelationDecision.incident_id==id).order_by(RelationDecision.created_at.desc()).limit(50))]
    return result

@router.post('/api/v1/admin/incidencias/{id}/relaciones')
def decide_relation(id:str,body:RelationInput,user=Depends(staff),db=Depends(get_db)):
    row=get_incident(db,id)
    other=get_incident(db,body.relacionado_id)
    if row.id==other.id or other.created_at>row.created_at:
        raise HTTPException(422,'No se admiten relaciones con el propio caso ni con casos posteriores')
    db.add(RelationDecision(incident_id=id,related_id=other.id,user_id=user.id,decision=body.decision,reason=anonymize(body.motivo)))
    db.add(Audit(user_id=user.id,action='relacion_pln',entity_id=id,changes={'relacionado_id':other.id,'decision':body.decision}))
    db.commit()
    return {'registrada':True,'fusion_realizada':False}
