"""
Local Transformers implementation of BaseLLMProvider — runs a model on
this machine/GPU via `transformers` instead of a hosted API. Useful for
open-weight models and for keeping the pipeline runnable at zero API cost.

Belongs to: backend/app/llm/providers/
Phase: 4 (LLM Generation Service)
"""
import asyncio
import time

from app.llm.base_provider import BaseLLMProvider, GenerationResult
from app.llm.providers.openai_provider import extract_code


class LocalModelProvider(BaseLLMProvider):
    def __init__(self, model_name: str):
        self._model_name = model_name
        self._pipeline = None  # lazy-loaded: avoid paying model load cost at import time

    def _load(self):
        if self._pipeline is None:
            from transformers import pipeline  # imported lazily: heavy dependency

            self._pipeline = pipeline("text-generation", model=self._model_name)
        return self._pipeline

    async def generate_code(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024
    ) -> GenerationResult:
        # transformers' pipeline() is synchronous/blocking; run it in a
        # worker thread so it doesn't stall the event loop LLMManager uses
        # to fan out to other (async) providers concurrently.
        start = time.monotonic()
        raw_text = await asyncio.to_thread(self._run_sync, prompt, temperature, max_tokens)
        latency = time.monotonic() - start

        return GenerationResult(
            model_name=self._model_name,
            prompt=prompt,
            code=extract_code(raw_text),
            raw_response=raw_text,
            temperature=temperature,
            max_tokens=max_tokens,
            tokens_used=len(raw_text.split()),
            latency_seconds=latency,
            metadata={},
        )

    def _run_sync(self, prompt: str, temperature: float, max_tokens: int) -> str:
        pipe = self._load()
        outputs = pipe(
            prompt,
            max_new_tokens=max_tokens,
            temperature=max(temperature, 0.01),
            do_sample=temperature > 0,
        )
        return outputs[0]["generated_text"]

    def get_model_info(self) -> dict:
        return {"name": self._model_name, "provider": "local"}

    def estimate_cost(self, tokens_used: int) -> float:
        return 0.0  # local compute; no per-token API cost
