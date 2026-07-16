"""
Abstract interface every LLM provider must implement (Strategy pattern).

LLMManager depends on this interface, not on concrete providers, so a new
model (Claude, Mistral, a fine-tuned local model...) can be added by writing
one new file in providers/ without touching any calling code — Open/Closed
Principle.

Belongs to: backend/app/llm/
Phase: 4 (LLM Generation Service)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class GenerationResult:
    """Structured result returned by every provider's generate_code call."""
    model_name: str
    prompt: str
    code: str
    raw_response: str
    temperature: float
    max_tokens: int
    tokens_used: int
    latency_seconds: float
    metadata: dict[str, Any]


class BaseLLMProvider(ABC):
    """Every concrete provider (OpenAI, HuggingFace, local) implements this."""

    @abstractmethod
    async def generate_code(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> GenerationResult:
        """Generate a code solution for the given prompt."""
        raise NotImplementedError

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Return metadata about the underlying model (name, version, context window)."""
        raise NotImplementedError

    @abstractmethod
    def estimate_cost(self, tokens_used: int) -> float:
        """Estimate USD cost for a generation call, for experiment budgeting."""
        raise NotImplementedError
