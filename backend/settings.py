import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', encoding='utf-8-sig')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./demo.db')
APP_SECRET = os.getenv('APP_SECRET', '')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:8080').split(',')
COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
MODEL_MANIFEST = Path(os.getenv('MODEL_MANIFEST', str(ROOT / 'models/active.json')))
