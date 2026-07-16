def test_register_and_list_models(client):
    resp = client.post("/models", json={"name": "gpt-4", "provider": "openai"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "gpt-4"

    resp = client.get("/models")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "gpt-4" in names


def test_registering_same_model_twice_is_idempotent(client):
    client.post("/models", json={"name": "llama-3-70b", "provider": "huggingface"})
    client.post("/models", json={"name": "llama-3-70b", "provider": "huggingface"})
    resp = client.get("/models")
    names = [m["name"] for m in resp.json()]
    assert names.count("llama-3-70b") == 1
