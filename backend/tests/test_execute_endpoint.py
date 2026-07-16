"""End-to-end test of POST /solutions/{id}/execute with the sandbox mocked."""
import app.api.v1.solutions as solutions_module


def _fake_run_solution_in_sandbox(code, reference_tests):
    return {
        "passed_tests": 1,
        "total_tests": 1,
        "pass_rate": 1.0,
        "runtime_seconds": 0.01,
        "memory_mb": None,
        "stdout": "1 passed",
        "stderr": "",
        "error_type": None,
    }


def test_execute_solution_end_to_end(client, auth_headers, monkeypatch):
    monkeypatch.setattr(solutions_module, "run_solution_in_sandbox", _fake_run_solution_in_sandbox)

    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.post(
        "/experiments",
        headers=auth_headers,
        json={
            "name": "Addition",
            "prompts": [{
                "problem_statement": "Write add(a, b)",
                "reference_tests": [{"call": "add(1, 2)", "expected_output": 3}],
            }],
            "models": ["gpt-4"],
        },
    )
    experiment_id = resp.json()["id"]

    # Insert a solution directly via the DB session fixture (skips /generate
    # since that's exercised separately in test_generate_endpoint.py).
    from app.database import crud
    from app.database.session import get_db
    from app.main import app as fastapi_app

    db = next(fastapi_app.dependency_overrides[get_db]())
    experiment = crud.get_experiment(db, experiment_id)
    prompt = experiment.prompts[0]
    model = crud.get_model_by_name(db, "gpt-4")
    solution = crud.save_generated_solution(
        db, prompt_id=prompt.id, model_id=model.id, code="def add(a, b): return a + b",
        raw_response="...", temperature=0.2, max_tokens=100, tokens_used=10, latency_seconds=0.1,
    )

    resp = client.post(f"/solutions/{solution.id}/execute", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["pass_rate"] == 1.0

    resp = client.get(f"/solutions/{solution.id}", headers=auth_headers)
    assert resp.json()["pass_rate"] == 1.0


def test_execute_without_reference_tests_returns_422_not_500(client, auth_headers):
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.post(
        "/experiments",
        headers=auth_headers,
        json={"name": "No tests", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
    )
    experiment_id = resp.json()["id"]

    from app.database import crud
    from app.database.session import get_db
    from app.main import app as fastapi_app

    db = next(fastapi_app.dependency_overrides[get_db]())
    experiment = crud.get_experiment(db, experiment_id)
    prompt = experiment.prompts[0]
    model = crud.get_model_by_name(db, "gpt-4")
    solution = crud.save_generated_solution(
        db, prompt_id=prompt.id, model_id=model.id, code="def x(): pass",
        raw_response="...", temperature=0.2, max_tokens=100, tokens_used=5, latency_seconds=0.1,
    )

    resp = client.post(f"/solutions/{solution.id}/execute", headers=auth_headers)
    assert resp.status_code == 422
