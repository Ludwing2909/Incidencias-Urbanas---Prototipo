"""Creación explícita de usuarios locales con secretos externos aleatorios."""
import secrets
from dotenv import dotenv_values
from sqlalchemy import select
from backend.db import SessionLocal,User
from backend.security import hasher
from backend.settings import ROOT,DATABASE_URL

def main():
    if not DATABASE_URL.startswith('sqlite'):
        raise SystemExit('Este comando solo prepara la demo SQLite individual. Para PostgreSQL use create-user.')
    env=ROOT/'.env'
    if not env.exists():raise SystemExit('Primero ejecute scripts/init_env.ps1')
    values=dotenv_values(env,encoding='utf-8-sig')
    appended=[]
    with SessionLocal() as db:
        for username,role,key in [('admin-demo','administrador','DEMO_ADMIN_PASSWORD'),('revisor-demo','revisor','DEMO_REVIEWER_PASSWORD')]:
            if db.scalar(select(User).where(User.username==username)):
                continue
            password=values.get(key) or secrets.token_urlsafe(24)
            if key not in values:appended.append(f'{key}={password}')
            db.add(User(username=username,role=role,password_hash=hasher.hash(password)))
        # Guardar secretos externos antes de confirmar cuentas. No imprimirlos.
        if appended:
            with env.open('a',encoding='utf-8') as f:f.write('\n# Credenciales solo de demostración local\n'+'\n'.join(appended)+'\n')
        db.commit()
    print('Demo preparada. Usuarios: admin-demo y revisor-demo. Contraseñas en .env, nunca en logs.')

if __name__=='__main__':main()
