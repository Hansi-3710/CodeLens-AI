"""Tests OpenAIProvider's code-fence extraction — pure logic, no network."""
from app.llm.providers.openai_provider import extract_code


def test_extracts_code_from_fenced_block():
    text = "Here is a solution:\n```python\ndef add(a, b):\n    return a + b\n```\nHope that helps!"
    assert extract_code(text) == "def add(a, b):\n    return a + b"


def test_falls_back_to_raw_text_when_no_fence():
    text = "def add(a, b): return a + b"
    assert extract_code(text) == text


def test_extracts_first_fence_when_multiple_present():
    text = "```python\ndef a(): pass\n```\nand also\n```python\ndef b(): pass\n```"
    assert extract_code(text) == "def a(): pass"
