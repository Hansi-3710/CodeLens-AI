"""
Database engine/session management.

Belongs to: backend/app/database/
"""
import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Logs which host/db we're connecting to for startup debugging — deliberately
# NOT the full DATABASE_URL, which contains the password in plaintext and
# would otherwise leak into Render's (or any host's) persisted log output.
_safe_target = settings.DATABASE_URL.rsplit("@", 1)[-1] if "@" in settings.DATABASE_URL else "(local/sqlite)"
logger.info("Connecting to database at: %s", _safe_target)

# pool_pre_ping avoids handing out dead connections after a DB restart/idle
# timeout. pool_size/max_overflow are conservative defaults for a single
# backend instance; tune upward alongside DB max_connections in Phase 9.
# connect_timeout=10 is the important one operationally: without it, an
# unreachable host (wrong hostname, or — the specific real-world case that
# motivated adding this — a provider's IPv6-only connection string on a
# host with no IPv6 route, e.g. Supabase's direct connection string on
# Render) hangs indefinitely instead of failing fast. A silent hang here
# looks identical to "still building" in a deploy log for however long the
# platform's own timeout takes (Render: ~15 minutes) before finally giving
# up with a generic "no open ports detected" — nothing points at the real
# cause. Ten seconds converts that into an immediate, readable connection
# error instead.
# SQLite (used in tests, see tests/conftest.py) ignores connect_args/
# pool_size/max_overflow it doesn't support, so this engine is prod-only.
_engine_kwargs = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("postgresql"):
    _engine_kwargs.update(
        pool_size=5, max_overflow=10, pool_recycle=1800,
        connect_args={"connect_timeout": 10},
    )

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
