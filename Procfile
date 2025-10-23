web: python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
worker: python -m celery -A src.tasks worker --loglevel=info
