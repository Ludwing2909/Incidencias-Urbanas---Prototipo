import argparse
import getpass
import json
import secrets
from pathlib import Path
from sqlalchemy import select, delete
from backend.db import SessionLocal, User, Rule, Audit, RateBucket, LoginSession, now
from backend.security import hasher
from backend.settings import ROOT

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command',required=True)
    user = sub.add_parser('create-user')
    user.add_argument('--username',required=True)
    user.add_argument('--role',choices=['administrador','revisor'],required=True)
    sub.add_parser('seed-rules')
    sub.add_parser('purge-sessions-and-limits')
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == 'create-user':
            if db.scalar(select(User).where(User.username == args.username)):
                raise SystemExit('El usuario ya existe; no se modifica su contraseña')
            password = getpass.getpass('Contraseña nueva (mínimo 12 caracteres): ')
            if len(password) < 12:
                raise SystemExit('Contraseña demasiado corta')
            db.add(User(username=args.username,password_hash=hasher.hash(password),role=args.role))
        elif args.command == 'seed-rules':
            for item in json.loads((ROOT/'config/demo_rules.json').read_text(encoding='utf-8')):
                if not db.scalar(select(Rule).where(Rule.category == item['category'])):
                    db.add(Rule(**item))
        else:
            # Ejecutar en mantenimiento: los contadores activos se reinician.
            db.execute(delete(LoginSession).where(LoginSession.expires_at < now()))
            db.execute(delete(RateBucket))
        db.commit()
    print('Operación administrativa completada')

if __name__ == '__main__':
    main()
