"""
Seeds the AI model registry so experiments can be created against them
without a manual POST /models call first.

Belongs to: backend/scripts/
Phase: 3 (Database)

Usage:
    PYTHONPATH=. python scripts/seed.py
"""
from app.database import crud
from app.database.models import Base
from app.database.session import SessionLocal, engine

DEFAULT_MODELS = [
    {"name": "gpt-4", "provider": "openai", "version": "gpt-4-turbo", "context_window": 128_000},
    {"name": "gpt-4o-mini", "provider": "openai", "version": "gpt-4o-mini", "context_window": 128_000},
    {"name": "llama-3-70b", "provider": "huggingface", "version": "meta-llama/Meta-Llama-3-70B-Instruct", "context_window": 8_192},
    {"name": "gemma-7b", "provider": "huggingface", "version": "google/gemma-7b-it", "context_window": 8_192},
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)  # no-op if Alembic already migrated
    db = SessionLocal()
    try:
        for m in DEFAULT_MODELS:
            crud.create_model(db, **m)
            print(f"ensured model: {m['name']}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
