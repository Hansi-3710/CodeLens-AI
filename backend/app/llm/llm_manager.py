"""
LLMManager — fans a single prompt out to every requested provider
concurrently and normalizes results, isolating per-provider failures so one
model timing out never fails the whole batch.

Belongs to: backend/app/llm/
Phase: 4 (LLM Generation Service)
"""
import asyncio
import logging
from dataclasses import dataclass

from app.config import get_settings
from app.llm.base_provider import BaseLLMProvider, GenerationResult
from app.llm.providers.huggingface_provider import HuggingFaceProvider
from app.llm.providers.local_model_provider import LocalModelProvider
from app.llm.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


@dataclass
class ProviderError:
    """Returned in place of a GenerationResult when a provider fails, so
    the caller can distinguish "model refused/errored" from "no result yet"
    without an exception unwinding the whole batch."""
    model_name: str
    error: str


def build_provider(model_name: str, provider_type: str, version: str | None = None) -> BaseLLMProvider:
    """Factory: registered AIModel row -> concrete provider instance.

    `provider_type` comes from AIModel.provider (openai | huggingface | local),
    kept independent of the display `model_name` so e.g. two OpenAI models
    can share the OpenAIProvider class with different `model` kwargs.
    """
    settings = get_settings()
    if provider_type == "openai":
        return OpenAIProvider(api_key=settings.OPENAI_API_KEY or "", model=version or model_name)
    if provider_type == "huggingface":
        return HuggingFaceProvider(api_token=settings.HUGGINGFACE_API_TOKEN or "", model_id=version or model_name)
    if provider_type == "local":
        return LocalModelProvider(model_name=version or model_name)
    raise ValueError(f"Unknown provider type: {provider_type}")


class LLMManager:
    def __init__(self, providers: dict[str, BaseLLMProvider]):
        """providers: {registered_model_name: provider_instance}"""
        self._providers = providers

    async def generate_all(
        self, prompt: str, model_names: list[str], temperature: float = 0.2, max_tokens: int = 1024
    ) -> list[GenerationResult | ProviderError]:
        async def _run_one(name: str) -> GenerationResult | ProviderError:
            provider = self._providers.get(name)
            if provider is None:
                return ProviderError(model_name=name, error=f"No provider registered for '{name}'")
            try:
                return await provider.generate_code(prompt, temperature=temperature, max_tokens=max_tokens)
            except Exception as exc:  # noqa: BLE001 - intentionally broad: isolate ANY provider failure
                logger.warning("Provider %s failed to generate: %s", name, exc)
                return ProviderError(model_name=name, error=str(exc))

        return await asyncio.gather(*(_run_one(name) for name in model_names))
