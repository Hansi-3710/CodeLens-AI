"""
OpenAI-backed implementation of BaseLLMProvider (e.g. gpt-4, gpt-4o-mini).

Belongs to: backend/app/llm/providers/
Phase: 4 (LLM Generation Service)
"""
import re
import time

from openai import AsyncOpenAI

from app.llm.base_provider import BaseLLMProvider, GenerationResult

# USD per 1K tokens, input+output blended for estimation purposes only.
# Real billing should read actual usage from the API response, not this table.
_PRICING_PER_1K_TOKENS = {
    "gpt-4": 0.03,
    "gpt-4o-mini": 0.00015,
}

_CODE_FENCE_RE = re.compile(r"```(?:[a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Pulls the first fenced code block out of a model response, falling
    back to the raw text if the model didn't use markdown fences."""
    match = _CODE_FENCE_RE.search(text)
    return match.group(1).strip() if match else text.strip()


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        # A falsy api_key would make AsyncOpenAI raise immediately at
        # construction (recent SDK versions validate eagerly). We'd rather
        # fail per-provider when generate_code() actually calls the API —
        # consistent with LLMManager's error-isolation contract — than
        # crash the whole /generate request before any model is even tried.
        self._client = AsyncOpenAI(api_key=api_key or "not-configured")
        self._model = model

    async def generate_code(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024
    ) -> GenerationResult:
        system_prompt = (
            "You are an expert software engineer. Respond with ONLY a single "
            "fenced code block containing a complete, runnable solution."
        )
        start = time.monotonic()
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = time.monotonic() - start

        raw_text = response.choices[0].message.content or ""
        return GenerationResult(
            model_name=self._model,
            prompt=prompt,
            code=extract_code(raw_text),
            raw_response=raw_text,
            temperature=temperature,
            max_tokens=max_tokens,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            latency_seconds=latency,
            metadata={"finish_reason": response.choices[0].finish_reason},
        )

    def get_model_info(self) -> dict:
        return {"name": self._model, "provider": "openai"}

    def estimate_cost(self, tokens_used: int) -> float:
        rate = _PRICING_PER_1K_TOKENS.get(self._model, 0.03)
        return (tokens_used / 1000) * rate
