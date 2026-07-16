"""Tests build_provider()'s dispatch logic — constructing provider objects
without making any real network call."""
import pytest

from app.llm.llm_manager import build_provider
from app.llm.providers.huggingface_provider import HuggingFaceProvider
from app.llm.providers.local_model_provider import LocalModelProvider
from app.llm.providers.openai_provider import OpenAIProvider


def test_builds_openai_provider():
    provider = build_provider("gpt-4", "openai")
    assert isinstance(provider, OpenAIProvider)


def test_builds_huggingface_provider():
    provider = build_provider("llama-3-70b", "huggingface", version="meta-llama/Meta-Llama-3-70B-Instruct")
    assert isinstance(provider, HuggingFaceProvider)


def test_builds_local_provider():
    provider = build_provider("local-model", "local")
    assert isinstance(provider, LocalModelProvider)


def test_unknown_provider_type_raises():
    with pytest.raises(ValueError):
        build_provider("mystery", "unknown-provider-type")
