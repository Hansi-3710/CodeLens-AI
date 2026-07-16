"""
Tests LLMManager's fan-out and error isolation using fake providers —
no real network calls to OpenAI/HuggingFace (not reachable from this
environment, and shouldn't be required to trust the manager's own logic).
"""
import pytest

from app.llm.base_provider import BaseLLMProvider, GenerationResult
from app.llm.llm_manager import LLMManager, ProviderError


class FakeProvider(BaseLLMProvider):
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail

    async def generate_code(self, prompt, temperature=0.2, max_tokens=1024):
        if self.should_fail:
            raise RuntimeError("simulated provider outage")
        return GenerationResult(
            model_name=self.name,
            prompt=prompt,
            code=f"def solve():\n    return '{self.name}'",
            raw_response="```python\ndef solve(): ...\n```",
            temperature=temperature,
            max_tokens=max_tokens,
            tokens_used=42,
            latency_seconds=0.01,
            metadata={},
        )

    def get_model_info(self):
        return {"name": self.name, "provider": "fake"}

    def estimate_cost(self, tokens_used):
        return 0.0


@pytest.mark.asyncio
async def test_generate_all_returns_results_for_every_model():
    manager = LLMManager({"gpt-4": FakeProvider("gpt-4"), "gemma-7b": FakeProvider("gemma-7b")})
    results = await manager.generate_all("write binary search", ["gpt-4", "gemma-7b"])
    assert len(results) == 2
    assert all(isinstance(r, GenerationResult) for r in results)


@pytest.mark.asyncio
async def test_one_failing_provider_does_not_break_the_batch():
    manager = LLMManager({
        "gpt-4": FakeProvider("gpt-4"),
        "llama-3-70b": FakeProvider("llama-3-70b", should_fail=True),
    })
    results = await manager.generate_all("write binary search", ["gpt-4", "llama-3-70b"])
    assert len(results) == 2

    by_model = {r.model_name: r for r in results}
    assert isinstance(by_model["gpt-4"], GenerationResult)
    assert isinstance(by_model["llama-3-70b"], ProviderError)


@pytest.mark.asyncio
async def test_unregistered_model_name_returns_provider_error_not_exception():
    manager = LLMManager({"gpt-4": FakeProvider("gpt-4")})
    results = await manager.generate_all("write binary search", ["gpt-4", "not-a-real-model"])
    errors = [r for r in results if isinstance(r, ProviderError)]
    assert len(errors) == 1
    assert "not-a-real-model" in errors[0].error
