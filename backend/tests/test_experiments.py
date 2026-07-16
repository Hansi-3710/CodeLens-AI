def test_create_experiment_requires_known_models(client, auth_headers):
    resp = client.post(
        "/experiments",
        headers=auth_headers,
        json={
            "name": "Shortest path comparison",
            "prompts": [{"problem_statement": "Implement Dijkstra's algorithm."}],
            "models": ["gpt-4"],
        },
    )
    assert resp.status_code == 422  # gpt-4 not registered yet


def test_create_and_fetch_experiment(client, auth_headers):
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)

    resp = client.post(
        "/experiments",
        headers=auth_headers,
        json={
            "name": "Shortest path comparison",
            "prompts": [{"problem_statement": "Implement Dijkstra's algorithm."}],
            "models": ["gpt-4"],
        },
    )
    assert resp.status_code == 201
    experiment_id = resp.json()["id"]
    assert resp.json()["status"] == "pending"

    resp = client.get(f"/experiments/{experiment_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Shortest path comparison"


def test_cannot_fetch_another_users_experiment(client, auth_headers):
    client.post("/models", json={"name": "gpt-4", "provider": "openai"})
    resp = client.post(
        "/experiments",
        headers=auth_headers,
        json={"name": "Private", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
    )
    experiment_id = resp.json()["id"]

    client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
    other_login = client.post("/auth/login", data={"username": "other@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    resp = client.get(f"/experiments/{experiment_id}", headers=other_headers)
    assert resp.status_code == 404


def test_list_experiments_returns_only_current_users(client, auth_headers):
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    client.post(
        "/experiments", headers=auth_headers,
        json={"name": "Mine", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
    )

    client.post("/auth/register", json={"email": "other2@example.com", "password": "password123"})
    other_login = client.post("/auth/login", data={"username": "other2@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    client.post(
        "/experiments", headers=other_headers,
        json={"name": "Theirs", "prompts": [{"problem_statement": "y"}], "models": ["gpt-4"]},
    )

    resp = client.get("/experiments", headers=auth_headers)
    assert resp.status_code == 200
    names = [e["name"] for e in resp.json()]
    assert names == ["Mine"]


def test_delete_experiment_cascades_to_prompts_and_solutions(client, auth_headers):
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.post(
        "/experiments", headers=auth_headers,
        json={"name": "To delete", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
    )
    experiment_id = resp.json()["id"]

    resp = client.delete(f"/experiments/{experiment_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/experiments/{experiment_id}", headers=auth_headers)
    assert resp.status_code == 404


def test_cannot_delete_another_users_experiment(client, auth_headers):
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.post(
        "/experiments", headers=auth_headers,
        json={"name": "Private", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
    )
    experiment_id = resp.json()["id"]

    client.post("/auth/register", json={"email": "deleter@example.com", "password": "password123"})
    other_login = client.post("/auth/login", data={"username": "deleter@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    resp = client.delete(f"/experiments/{experiment_id}", headers=other_headers)
    assert resp.status_code == 404  # not 403 — existence isn't leaked, same as GET

    # Confirm it wasn't actually deleted by the failed attempt.
    resp = client.get(f"/experiments/{experiment_id}", headers=auth_headers)
    assert resp.status_code == 200


def test_deleting_nonexistent_experiment_returns_404_not_500(client, auth_headers):
    resp = client.delete("/experiments/does-not-exist", headers=auth_headers)
    assert resp.status_code == 404
