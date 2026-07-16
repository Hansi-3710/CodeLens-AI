"""
Smoke test proving the FastAPI app boots and wiring is correct.
This is the only test that should pass in Phase 1 — everything else
is legitimately a 501 until its owning phase lands.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unauthenticated_experiment_creation_is_rejected_not_500():
    """Guards against silently-broken routers: protected routes should fail
    loudly with a clear 401, never with an unhandled exception (500)."""
    response = client.post("/experiments", json={"name": "x", "prompts": [], "models": []})
    assert response.status_code == 401
