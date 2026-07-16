"""Proves an unhandled exception returns a sanitized 500 (no traceback/
internal details leaked) with a request ID, instead of FastAPI's default
debug-style error body."""
from fastapi.testclient import TestClient

from app.main import app


def test_unhandled_exception_returns_sanitized_body(monkeypatch):
    from app.api.v1 import models as models_router

    def _boom(db):
        raise RuntimeError("simulated internal failure with a fake db password=hunter2 in it")

    monkeypatch.setattr(models_router.crud, "list_models", _boom)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/models")

    assert resp.status_code == 500
    body = resp.json()
    assert body["detail"] == "Internal server error"
    assert "request_id" in body
    # The real exception message (which could contain secrets) must never
    # reach the client — this is the actual security property being tested.
    assert "hunter2" not in resp.text
    assert "RuntimeError" not in resp.text


def test_every_response_carries_a_request_id_header():
    client = TestClient(app)
    resp = client.get("/health")
    assert "X-Request-ID" in resp.headers
