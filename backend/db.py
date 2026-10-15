from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine, event, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from backend.settings import DATABASE_URL

def now():
    return datetime.now(timezone.utc)

def uid():
    return str(uuid4())

class Base(DeclarativeBase):
    """Registro declarativo SQLAlchemy."""

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False, 'timeout': 30} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def sqlite_settings(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA journal_mode=WAL')
SessionLocal = sessionmaker(engine, expire_on_commit=False)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20))

class LoginSession(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class RateBucket(Base):
    __tablename__ = 'rate_buckets'
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)

class YearSequence(Base):
    __tablename__ = 'year_sequences'
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[int] = mapped_column(Integer)

class Incident(Base):
    __tablename__ = 'incidents'
    __table_args__ = (UniqueConstraint('year', 'sequence'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    year: Mapped[int] = mapped_column(Integer)
    sequence: Mapped[int] = mapped_column(Integer)
    secret_hash: Mapped[str] = mapped_column(String(64))
    idempotency_hash: Mapped[str] = mapped_column(String(64), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(180))
    state: Mapped[str] = mapped_column(String(40))
    current_topic: Mapped[str | None] = mapped_column(String(2))
    current_destination: Mapped[str | None] = mapped_column(String(200))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Prediction(Base):
    __tablename__ = 'predictions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey('incidents.id'), unique=True)
    result: Mapped[dict] = mapped_column(JSON)
    latency_ms: Mapped[int] = mapped_column(Integer)

class Review(Base):
    __tablename__ = 'reviews'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey('incidents.id'))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    original_topic: Mapped[str | None] = mapped_column(String(2))
    topic: Mapped[str | None] = mapped_column(String(2))
    original_destination: Mapped[str | None] = mapped_column(String(200))
    destination: Mapped[str | None] = mapped_column(String(200))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class StateHistory(Base):
    __tablename__ = 'state_history'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey('incidents.id'))
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    previous: Mapped[str | None] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Rule(Base):
    __tablename__ = 'rules'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    category: Mapped[str] = mapped_column(String(2))
    territory: Mapped[str] = mapped_column(String(180))
    destination: Mapped[str] = mapped_column(String(200))
    conditions: Mapped[str] = mapped_column(Text)
    validated: Mapped[bool] = mapped_column(Boolean, default=False)
    valid_from: Mapped[str] = mapped_column(String(10))
    valid_until: Mapped[str] = mapped_column(String(10))
    source: Mapped[str] = mapped_column(Text)
    responsible: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class ModelVersion(Base):
    __tablename__ = 'model_versions'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    manifest: Mapped[dict] = mapped_column(JSON)
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Audit(Base):
    __tablename__ = 'audit'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str] = mapped_column(String(100))
    changes: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class AnalysisVersion(Base):
    __tablename__ = 'analysis_versions'
    __table_args__ = (UniqueConstraint('incident_id','version'),)
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey('incidents.id'))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    version: Mapped[int] = mapped_column(Integer)
    original_text: Mapped[str] = mapped_column(Text)
    answers: Mapped[dict] = mapped_column(JSON)
    analysis: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)

class RelationDecision(Base):
    __tablename__ = 'relation_decisions'
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey('incidents.id'))
    related_id: Mapped[str] = mapped_column(ForeignKey('incidents.id'))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    decision: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)

def get_db():
    with SessionLocal() as db:
        yield db
