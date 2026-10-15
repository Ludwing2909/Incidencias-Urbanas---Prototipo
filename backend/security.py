import hashlib
import hmac
import secrets
import time
from datetime import timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from backend.db import get_db, LoginSession, User, RateBucket, now
from backend.settings import APP_SECRET

hasher = PasswordHasher()
DUMMY_HASH = hasher.hash('no-valid-user-password')

def digest(value):
    return hmac.new(APP_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()

def verify_password(encoded, password):
    try:
        return hasher.verify(encoded, password)
    except VerificationError:
        return False

def limit(db, request, kind, maximum):
    # IP del socket: no se confía en X-Forwarded-For. Compartido entre procesos.
    key = digest(f'{kind}:{request.client.host if request.client else "test"}:{int(time.time() // 600)}')
    insert = sqlite_insert if db.bind.dialect.name == 'sqlite' else pg_insert
    stmt = insert(RateBucket).values(key=key, count=1).on_conflict_do_update(index_elements=['key'], set_={'count': RateBucket.count + 1}).returning(RateBucket.count)
    count = db.execute(stmt).scalar_one()
    db.commit()
    if count > maximum:
        raise HTTPException(429, 'Demasiados intentos; espere diez minutos')

def staff(request: Request, db=Depends(get_db)):
    token = request.cookies.get('session', '')
    session = db.get(LoginSession, digest(token)) if token else None
    expiry = session.expires_at.replace(tzinfo=timezone.utc) if session else now()
    if not session or expiry <= now():
        raise HTTPException(401, 'Inicie sesión')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        csrf = request.headers.get('X-CSRF-Token', '')
        if not csrf or not hmac.compare_digest(digest(csrf), session.csrf_hash):
            raise HTTPException(403, 'Token CSRF inválido')
    user = db.get(User, session.user_id)
    if not user or user.role not in ('administrador', 'revisor'):
        raise HTTPException(403, 'Sin permisos')
    return user

def admin(user=Depends(staff)):
    if user.role != 'administrador':
        raise HTTPException(403, 'Se requiere administrador')
    return user

def create_session(db, user):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.add(LoginSession(token_hash=digest(token), user_id=user.id, csrf_hash=digest(csrf), expires_at=now() + timedelta(hours=8)))
    db.commit()
    return token, csrf
