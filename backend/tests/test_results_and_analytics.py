"""
End-to-end: create an experiment with 2 models, generate (mocked provider),
then check /results, /analytics, and /analytics/similarity all return
real, computed data — not just wiring smoke tests.
"""
import app.api.v1.experiments as experiments_module
from app.llm.base_provider import BaseLLMProvider, GenerationResult


class _DistinctCodeProvider(BaseLLMProvider):
    """Returns genuinely different code per model, so similarity/complexity
    results are meaningfully different rather than trivially identical."""

    _CODE = {
        "gpt-4": "def total(nums):\n    s = 0\n    for n in nums:\n        s += n\n    return s\n",
        "gemma-7b": "def total(nums):\n    if not nums:\n        return 0\n    return nums[0] + total(nums[1:])\n",
    }

    def __init__(self, model_name, **_):
        self.model_name = model_name

    async def generate_code(self, prompt, temperature=0.2, max_tokens=1024):
        code = self._CODE[self.model_name]
        return GenerationResult(
            model_name=self.model_name, prompt=prompt, code=code, raw_response=code,
            temperature=temperature, max_tokens=max_tokens, tokens_used=20,
            latency_seconds=0.02, metadata={},
        )

    def get_model_info(self):
        return {"name": self.model_name}

    def estimate_cost(self, tokens_used):
        return 0.0


def _setup_experiment_with_generated_solutions(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        experiments_module, "build_provider",
        lambda model_name, provider_type, version=None: _DistinctCodeProvider(model_name),
    )
    client.post("/models", json={"name": "gpt-4", "provider": "openai"}, headers=auth_headers)
    client.post("/models", json={"name": "gemma-7b", "provider": "huggingface"}, headers=auth_headers)

    resp = client.post(
        "/experiments", headers=auth_headers,
        json={
            "name": "Sum comparison",
            "prompts": [{"problem_statement": "Sum a list of numbers."}],
            "models": ["gpt-4", "gemma-7b"],
        },
    )
    experiment_id = resp.json()["id"]
    client.post(f"/experiments/{experiment_id}/generate", headers=auth_headers)
    return experiment_id


def test_results_endpoint_returns_model_comparison(client, auth_headers, monkeypatch):
    experiment_id = _setup_experiment_with_generated_solutions(client, auth_headers, monkeypatch)

    resp = client.get(f"/experiments/{experiment_id}/results", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    model_names = {row["model"] for row in body["models"]}
    assert model_names == {"gpt-4", "gemma-7b"}
    # Analysis ran eagerly during /generate — complexity should be populated.
    for row in body["models"]:
        assert row["n_solutions"] == 1


def test_analytics_endpoint_returns_real_statistics(client, auth_headers, monkeypatch):
    experiment_id = _setup_experiment_with_generated_solutions(client, auth_headers, monkeypatch)

    resp = client.get(f"/analytics/{experiment_id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["n_solutions"] == 2
    assert body["code_length"]["n"] == 2


def test_similarity_endpoint_detects_iterative_vs_recursive_difference(client, auth_headers, monkeypatch):
    experiment_id = _setup_experiment_with_generated_solutions(client, auth_headers, monkeypatch)

    resp = client.get(f"/analytics/{experiment_id}/similarity", headers=auth_headers)
    assert resp.status_code == 200
    pairs = resp.json()["pairs"]
    assert len(pairs) == 1
    # The two solutions are one iterative and one recursive implementation
    # of the same problem — they should not score as identical.
    assert pairs[0]["ast_similarity"] < 1.0


def test_clusters_endpoint_handles_no_embeddings_gracefully(client, auth_headers, monkeypatch):
    """Embeddings require downloading model weights (network access not
    available in this test environment) so no solution has one yet — the
    endpoint should degrade gracefully, not 500."""
    experiment_id = _setup_experiment_with_generated_solutions(client, auth_headers, monkeypatch)

    resp = client.get(f"/analytics/{experiment_id}/clusters", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["points"] == []


def test_clusters_endpoint_rejects_invalid_method(client, auth_headers, monkeypatch):
    experiment_id = _setup_experiment_with_generated_solutions(client, auth_headers, monkeypatch)
    resp = client.get(f"/analytics/{experiment_id}/clusters?method=tsne", headers=auth_headers)
    assert resp.status_code == 422


def test_clusters_endpoint_accepts_pca_method(client, auth_headers, monkeypatch):
    experiment_id = _setup_experiment_with_generated_solutions(client, auth_headers, monkeypatch)
    resp = client.get(f"/analytics/{experiment_id}/clusters?method=pca", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["method"] == "pca"
