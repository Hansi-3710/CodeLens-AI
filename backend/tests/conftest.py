"""
Shared pytest fixtures: an isolated in-memory SQLite database per test
(fast, no external services needed) with FastAPI's get_db dependency
overridden to use it.

Note: production runs on PostgreSQL (see app/config.py DATABASE_URL).
SQLite is used here purely as a fast, dependency-free test double — the ORM
layer doesn't use any Postgres-specific column types, so behavior parity
is high, but true integration tests against Postgres belong in CI
(.github/workflows/ci.yml already spins up a real Postgres service).

Belongs to: backend/tests/
Phase: 2 (Backend Foundation)
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database.models import Base
from app.database.session import get_db
from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The rate limiter's default in-memory storage is process-global, not
    per-request — without resetting it, tests that hit /auth/register or
    /auth/login (most of them, via the auth_headers fixture below)
    accumulate real hits against the same counter and eventually trip a
    genuine 429 mid-suite, unrelated to whatever that test is actually
    checking. Production uses the same in-memory default per instance
    (see rate_limit.py's docstring on swapping to Redis for multi-instance
    deployments) — this fixture only resets the counter between tests, it
    doesn't change the limiter's behavior within a single request.
    """
    limiter.reset()
    yield


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite doesn't enforce FK constraints by default; turn them on so
    # cascade/ordering bugs surface in tests instead of only in Postgres.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    # Background tasks (e.g. /generate's _run_generation_job) don't go
    # through Depends(get_db) — they open their own session via
    # db_session_module.SessionLocal() because the request-scoped session
    # is already closed by the time a background task runs. Redirect that
    # factory to a sessionmaker bound to *this test's* engine (same
    # StaticPool, so it sees the same in-memory data as db_session) —
    # otherwise it falls through to the real SessionLocal from
    # app/database/session.py, which points at the production DATABASE_URL.
    import app.database.session as db_session_module
    original_session_local = db_session_module.SessionLocal
    db_session_module.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_session.get_bind()
    )

    with TestClient(app) as test_client:
        yield test_client

    db_session_module.SessionLocal = original_session_local
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Registers a user, logs in, returns {"Authorization": "Bearer ..."}."""
    client.post("/auth/register", json={"email": "researcher@example.com", "password": "supersecret123"})
    resp = client.post(
        "/auth/login",
        data={"username": "researcher@example.com", "password": "supersecret123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
