"""
Database engine/session management.

Belongs to: backend/app/database/
Phase: 3 (Database) for real connection pooling tuned to production; a
working default is included now since it's pure boilerplate.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# pool_pre_ping avoids handing out dead connections after a DB restart/idle
# timeout. pool_size/max_overflow are conservative defaults for a single
# backend instance; tune upward alongside DB max_connections in Phase 9.
# SQLite (used in tests, see tests/conftest.py) ignores the pool_size/
# max_overflow kwargs it doesn't support, so this engine is prod-only.
_engine_kwargs = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("postgresql"):
    _engine_kwargs.update(pool_size=5, max_overflow=10, pool_recycle=1800)

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
