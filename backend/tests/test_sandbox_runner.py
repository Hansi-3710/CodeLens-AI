"""Tests render_test_file()'s harness generation — pure logic, no Docker."""
from app.execution.sandbox_runner import render_test_file


def test_renders_one_test_function_per_case():
    tests = [
        {"call": "add(1, 2)", "expected_output": 3},
        {"call": "add(-1, 1)", "expected_output": 0},
    ]
    rendered = render_test_file(tests)
    assert "def test_case_0():" in rendered
    assert "def test_case_1():" in rendered
    assert "assert add(1, 2) == 3" in rendered
    assert "assert add(-1, 1) == 0" in rendered
    assert "from solution import *" in rendered


def test_renders_string_expected_output_with_quotes():
    tests = [{"call": "greet('Ada')", "expected_output": "Hello, Ada"}]
    rendered = render_test_file(tests)
    assert "== 'Hello, Ada'" in rendered
