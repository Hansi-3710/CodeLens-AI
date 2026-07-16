"""
Tests the full POST /experiments/{id}/generate flow end-to-end against the
in-memory test DB, with build_provider monkeypatched to a fake provider so
no real network call to OpenAI/HuggingFace is made.
"""
from app.llm.base_provider import BaseLLMProvider, GenerationResult
import app.api.v1.experiments as experiments_module


class _AlwaysWorksProvider(BaseLLMProvider):
    def __init__(self, model_name, **_):
        self.model_name = model_name

    async def generate_code(self, prompt, temperature=0.2, max_tokens=1024):
        return GenerationResult(
            model_name=self.model_name,
            prompt=prompt,
            code="def solve():\n    return 42",
            raw_response="```python\ndef solve():\n    return 42\n```",
            temperature=temperature,
            max_tokens=max_tokens,
            tokens_used=10,
            latency_seconds=0.01,
            metadata={},
        )

    def get_model_info(self):
        return {"name": self.model_name}

    def estimate_cost(self, tokens_used):
        return 0.0


def test_generate_creates_solutions_for_every_registered_model(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        experiments_module,
        "build_provider",
        lambda model_name, provider_type, version=None: _AlwaysWorksProvider(model_name),
    )

    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    client.post("/models", json={"name": "gemma-7b", "provider": "huggingface"}, headers=auth_headers)

    resp = client.post(
        "/experiments",
        headers=auth_headers,
        json={
            "name": "Shortest path",
            "prompts": [{"problem_statement": "Implement Dijkstra's algorithm."}],
            "models": ["gpt-4", "gemma-7b"],
        },
    )
    experiment_id = resp.json()["id"]

    resp = client.post(f"/experiments/{experiment_id}/generate", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"  # /generate returns immediately; work happens in a background task

    resp = client.get(f"/experiments/{experiment_id}", headers=auth_headers)
    assert resp.json()["status"] == "completed"


def test_generate_rejects_when_no_active_models_registered(client, auth_headers, monkeypatch):
    """Guards against a 500 when an experiment references a model that
    exists but has since been deactivated (is_active=False)."""
    monkeypatch.setattr(
        experiments_module,
        "build_provider",
        lambda model_name, provider_type, version=None: _AlwaysWorksProvider(model_name),
    )
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.post(
        "/experiments",
        headers=auth_headers,
        json={"name": "Test", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
    )
    experiment_id = resp.json()["id"]

    from app.database import crud
    from app.database.session import get_db
    from app.main import app as fastapi_app

    db = next(fastapi_app.dependency_overrides[get_db]())
    model = crud.get_model_by_name(db, "gpt-4")
    model.is_active = False
    db.commit()

    resp = client.post(f"/experiments/{experiment_id}/generate", headers=auth_headers)
    assert resp.status_code == 422
    assert resp.status_code != 500


def test_list_solutions_endpoint_returns_code_grouped_by_prompt(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        experiments_module,
        "build_provider",
        lambda model_name, provider_type, version=None: _AlwaysWorksProvider(model_name),
    )
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.post(
        "/experiments", headers=auth_headers,
        json={"name": "X", "prompts": [{"problem_statement": "Implement Dijkstra."}], "models": ["gpt-4"]},
    )
    experiment_id = resp.json()["id"]
    client.post(f"/experiments/{experiment_id}/generate", headers=auth_headers)

    resp = client.get(f"/experiments/{experiment_id}/solutions", headers=auth_headers)
    assert resp.status_code == 200
    solutions = resp.json()
    assert len(solutions) == 1
    assert solutions[0]["model_name"] == "gpt-4"
    assert "problem_statement" in solutions[0]


def test_generate_response_shape_is_running_not_completed(client, auth_headers, monkeypatch):
    """Direct test of the background-task architecture change itself: the
    endpoint's own response must reflect 'work has been scheduled', not
    'work is done' — the actual generation happens after the response is
    already on the wire (see _run_generation_job's docstring)."""
    monkeypatch.setattr(
        experiments_module,
        "build_provider",
        lambda model_name, provider_type, version=None: _AlwaysWorksProvider(model_name),
    )
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.post(
        "/experiments", headers=auth_headers,
        json={"name": "X", "prompts": [{"problem_statement": "p"}], "models": ["gpt-4"]},
    )
    experiment_id = resp.json()["id"]

    resp = client.post(f"/experiments/{experiment_id}/generate", headers=auth_headers)
    assert resp.json() == {"experiment_id": experiment_id, "status": "running"}


def test_generate_job_marks_experiment_failed_on_unexpected_error(client, auth_headers, monkeypatch):
    """The background job's own exception handling — not just the happy
    path — must leave the experiment in a terminal 'failed' state rather
    than stuck at 'running' forever with no way for the frontend to know
    generation isn't coming back."""
    def _broken_provider(model_name, provider_type, version=None):
        raise RuntimeError("simulated catastrophic provider construction failure")

    monkeypatch.setattr(experiments_module, "build_provider", _broken_provider)

    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.post(
        "/experiments", headers=auth_headers,
        json={"name": "X", "prompts": [{"problem_statement": "p"}], "models": ["gpt-4"]},
    )
    experiment_id = resp.json()["id"]

    client.post(f"/experiments/{experiment_id}/generate", headers=auth_headers)

    resp = client.get(f"/experiments/{experiment_id}", headers=auth_headers)
    assert resp.json()["status"] == "failed"


def test_generate_only_uses_models_selected_at_creation_not_every_registered_model(
    client, auth_headers, monkeypatch
):
    """Regression test for a real bug caught by live-testing against a real
    Postgres instance: /experiments POST accepted and validated a `models`
    list but never persisted it, so /generate silently ran against every
    active registered model instead of just the ones the user selected.
    This test registers 4 models but selects only 2, and asserts exactly
    those 2 (and no others) get solutions."""
    monkeypatch.setattr(
        experiments_module, "build_provider",
        lambda model_name, provider_type, version=None: _AlwaysWorksProvider(model_name),
    )
    for name in ["gpt-4", "gpt-4o-mini", "llama-3-70b", "gemma-7b"]:
        client.post("/models", json={"name": name, "provider": "openai"}, headers=auth_headers)

    resp = client.post(
        "/experiments", headers=auth_headers,
        json={
            "name": "Selective comparison",
            "prompts": [{"problem_statement": "Reverse a linked list."}],
            "models": ["gpt-4", "llama-3-70b"],  # deliberately not all 4 registered models
        },
    )
    experiment_id = resp.json()["id"]
    assert set(resp.json()["selected_models"]) == {"gpt-4", "llama-3-70b"}

    client.post(f"/experiments/{experiment_id}/generate", headers=auth_headers)

    resp = client.get(f"/experiments/{experiment_id}/solutions", headers=auth_headers)
    model_names = {s["model_name"] for s in resp.json()}
    assert model_names == {"gpt-4", "llama-3-70b"}, (
        f"expected only the 2 selected models, got solutions from: {model_names}"
    )
