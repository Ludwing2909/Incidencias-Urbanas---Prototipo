FROM python:3.12.10-slim
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY backend backend
COPY ml ml
COPY config config
COPY alembic.ini .
RUN useradd --uid 10001 --create-home appuser
USER appuser
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --no-access-log"]
