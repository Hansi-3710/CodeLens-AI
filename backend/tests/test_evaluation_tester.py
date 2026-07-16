from app.evaluation.tester import load_problems


def test_load_custom_problems_returns_well_formed_prompts():
    problems = load_problems("custom")
    assert len(problems) >= 5
    for p in problems:
        assert p["problem_statement"]
        assert p["language"] == "python"
        assert isinstance(p["reference_tests"], list)
        assert all("call" in t and "expected_output" in t for t in p["reference_tests"])


def test_load_unknown_source_raises_value_error():
    import pytest
    with pytest.raises(ValueError):
        load_problems("humaneval")
