"""
Hugging Face Inference API implementation of BaseLLMProvider
(e.g. Llama, Gemma, Mistral hosted models).

Belongs to: backend/app/llm/providers/
Phase: 4 (LLM Generation Service)
"""
import time

from huggingface_hub import AsyncInferenceClient

from app.llm.base_provider import BaseLLMProvider, GenerationResult
from app.llm.providers.openai_provider import extract_code


class HuggingFaceProvider(BaseLLMProvider):
    def __init__(self, api_token: str, model_id: str):
        self._client = AsyncInferenceClient(model=model_id, token=api_token)
        self._model_id = model_id

    async def generate_code(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024
    ) -> GenerationResult:
        formatted_prompt = (
            "You are an expert software engineer. Respond with ONLY a single "
            f"fenced code block containing a complete, runnable solution.\n\n{prompt}"
        )
        start = time.monotonic()
        # text_generation retries internally on model cold-start (503) by
        # default in huggingface_hub; no extra retry loop needed here.
        raw_text = await self._client.text_generation(
            formatted_prompt,
            max_new_tokens=max_tokens,
            temperature=max(temperature, 0.01),  # HF rejects temperature=0
        )
        latency = time.monotonic() - start

        return GenerationResult(
            model_name=self._model_id,
            prompt=prompt,
            code=extract_code(raw_text),
            raw_response=raw_text,
            temperature=temperature,
            max_tokens=max_tokens,
            tokens_used=len(raw_text.split()),  # HF doesn't always return token counts
            latency_seconds=latency,
            metadata={},
        )

    def get_model_info(self) -> dict:
        return {"name": self._model_id, "provider": "huggingface"}

    def estimate_cost(self, tokens_used: int) -> float:
        return 0.0  # Inference API usage is billed separately/on quota, not per-call here
