from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from ml.text import normalize

Category = Literal['C1','C2','C3','C4','C5','C6','C7','C8']
State = Literal['Pendiente de revisión','Sugerencia disponible','Revisado','Derivado','Resuelto']

class IncidentInput(BaseModel):
    descripcion: str = Field(min_length=1, max_length=3000)
    ubicacion_general: str | None = Field(default=None, max_length=180)
    @field_validator('descripcion')
    @classmethod
    def clean(cls, value):
        value = normalize(value)
        if not value:
            raise ValueError('La descripción no puede estar vacía')
        return value

class FollowInput(BaseModel):
    codigo: str = Field(min_length=1, max_length=30)
    secreto: str = Field(min_length=16, max_length=200)

class LoginInput(BaseModel):
    usuario: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)

class ReviewInput(BaseModel):
    tema: Category | None
    destino: str | None = Field(default=None, max_length=200)
    motivo: str = Field(min_length=8, max_length=1500)
    version: int = Field(ge=1)
    @field_validator('motivo')
    @classmethod
    def reason(cls, v):
        if len(v.strip()) < 8:
            raise ValueError('Explique la actuación con al menos 8 caracteres')
        return v.strip()

class TransitionInput(BaseModel):
    estado: State
    motivo: str = Field(min_length=8, max_length=1500)
    evidencia: str | None = Field(default=None, max_length=1500)
    confirmacion_humana: bool = False
    version: int = Field(ge=1)
    @field_validator('motivo')
    @classmethod
    def reason(cls, v):
        if len(v.strip()) < 8:
            raise ValueError('El motivo no puede ser espacios')
        return v.strip()

class RuleInput(BaseModel):
    category: Category
    territory: str = Field(min_length=1, max_length=180)
    destination: str = Field(min_length=1, max_length=200)
    conditions: str = Field(min_length=1, max_length=1500)
    validated: bool = False
    valid_from: date
    valid_until: date
    source: str = Field(min_length=1, max_length=1500)
    responsible: str = Field(min_length=1, max_length=100)
    version: int = Field(default=1, ge=1)
    active: bool = True
    @model_validator(mode='after')
    def dates(self):
        if self.valid_until < self.valid_from:
            raise ValueError('Vigencia inválida')
        if self.validated and (len(self.source.strip()) < 10 or len(self.responsible.strip()) < 3):
            raise ValueError('Validación requiere fuente documental y responsable')
        return self

class Classification(BaseModel):
    tema: Category | None
    tipo_puntuacion: Literal['probabilidad_calibrada','probabilidad','margen'] | None
    puntuacion: float | None
    requiere_revision: bool
    motivos_revision: list[str]
    ruta_revision: Literal['R9'] | None
    destino_sugerido: str | None
    prioridad: Literal['alta','media','baja','ordinaria','posible urgencia']
    evaluacion_prioridad: dict | None = None
    alerta_posible_urgencia: bool
    motivo_urgencia: str | None
    estado: State
    version_modelo: str | None
    version_umbral: str | None
    version_reglas: str | None
    demostrativo: bool
    destino: dict | None = None

class Registration(BaseModel):
    id: str
    codigo: str
    secreto_seguimiento: str
    clasificacion: Classification

class FollowEvent(BaseModel):
    estado: State
    fecha: datetime

class FollowResult(BaseModel):
    codigo: str
    estado: State
    fecha: datetime
    cronologia: list[FollowEvent]

class IncidentSummary(BaseModel):
    id: str
    code: str
    year: int
    sequence: int
    state: State
    current_topic: Category | None
    current_destination: str | None
    revision: int
    created_at: datetime

class IncidentPage(BaseModel):
    items: list[IncidentSummary]
    total: int
    page: int
    size: int

class IncidentDetail(IncidentSummary):
    texto: str
    ubicacion_general: str | None
    prediccion: Classification
    latencia_ms: int
    revisiones: list[dict]
    historial: list[dict]

class RuleResult(RuleInput):
    id: str

class StateResult(BaseModel):
    estado: State
    version: int

class LoginResult(BaseModel):
    usuario: str
    rol: Literal['administrador','revisor']
    csrf_token: str

class StatsResult(BaseModel):
    total: int
    por_categoria: dict[Category,int]
    sin_tema: int
    por_estado: dict[str,int]
    motivos_revision: dict[str,int]
    revisados: int
    correcciones: int
    latencia_media_ms: float | None
    tasa_revision_inicial: float | None
    correcciones_por_categoria: dict[str,int] = Field(default_factory=dict)

class ModelResult(BaseModel):
    disponible: bool
    motivo: str | None
    manifiesto: dict
    limites: list[str]

class AnalysisInput(BaseModel):
    descripcion: str = Field(min_length=1, max_length=3000)
    ubicacion_general: str | None = Field(default=None, max_length=180)

class TraceStage(BaseModel):
    id: str
    nombre: str
    estado: Literal['aplicada','omitida','no implementada','no disponible']
    motivo: str
    entrada: dict = Field(default_factory=dict)
    salida: dict = Field(default_factory=dict)
    transformaciones: list[str] = Field(default_factory=list)
    version: str | None = None
    tiempo_ms: float
    limitacion: str | None = None

class AnalysisResult(BaseModel):
    version_traza: str
    version_modelo: str | None
    valida: bool
    simulacion: bool = True
    etapas: list[TraceStage]
    clasificacion: Classification | None
    extraccion: dict
    preguntas: list[dict]
    tiempo_total_ms: float

class ClarificationInput(BaseModel):
    version: int = Field(ge=1)
    respuestas: dict[str, str]
    @field_validator('respuestas')
    @classmethod
    def bounded(cls, v):
        if not 1 <= len(v) <= 3 or any(not s.strip() or len(s) > 400 for s in v.values()):
            raise ValueError('Responda de una a tres preguntas con hasta 400 caracteres cada una')
        return v

class RelationInput(BaseModel):
    relacionado_id: str = Field(min_length=36, max_length=36)
    decision: Literal['confirmar','descartar']
    motivo: str = Field(min_length=8, max_length=1000)
    @field_validator('motivo')
    @classmethod
    def nonempty(cls, v):
        if len(v.strip()) < 8:
            raise ValueError('Explique la decisión')
        return v.strip()

class ExtractionCorrectionInput(BaseModel):
    version: int = Field(ge=1)
    campos: dict[str,str | None]
    @field_validator('campos')
    @classmethod
    def allowed(cls,v):
        allowed={'problema_principal','lugar_general','referencia_temporal'}
        if not v or not set(v).issubset(allowed) or any(s is not None and (not s.strip() or len(s)>400) for s in v.values()):
            raise ValueError('Corrija campos de extracción con fragmentos de hasta 400 caracteres o null')
        return v
