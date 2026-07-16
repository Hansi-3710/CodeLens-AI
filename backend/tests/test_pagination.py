def test_experiment_list_respects_limit(client, auth_headers):
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    for i in range(5):
        client.post(
            "/experiments", headers=auth_headers,
            json={"name": f"Exp {i}", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
        )

    resp = client.get("/experiments?limit=2", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_experiment_list_newest_first(client, auth_headers):
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    client.post(
        "/experiments", headers=auth_headers,
        json={"name": "First", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
    )
    client.post(
        "/experiments", headers=auth_headers,
        json={"name": "Second", "prompts": [{"problem_statement": "x"}], "models": ["gpt-4"]},
    )

    resp = client.get("/experiments", headers=auth_headers)
    names = [e["name"] for e in resp.json()]
    assert names == ["Second", "First"]


def test_experiment_list_limit_is_capped_at_100(client, auth_headers):
    """A malicious or buggy ?limit=999999 must not force an unbounded scan."""
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    resp = client.get("/experiments?limit=999999", headers=auth_headers)
    assert resp.status_code == 200  # doesn't error; the cap is applied silently server-side


def test_models_list_respects_limit(client, auth_headers):
    for name in ["gpt-4", "gpt-4o-mini", "llama-3-70b"]:
        client.post("/models", json={"name": name, "provider": "openai"}, headers=auth_headers)

    resp = client.get("/models?limit=1", headers=auth_headers)
    assert len(resp.json()) == 1
