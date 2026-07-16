"""Pure-function tests for result_parser.py — no Docker needed."""
from app.execution.result_parser import classify_error, parse_pytest_report


def test_all_tests_passed():
    report = {"summary": {"total": 3, "passed": 3}, "duration": 0.12}
    result = parse_pytest_report(report, stdout="", stderr="", timed_out=False, wall_time_seconds=0.2)
    assert result["passed_tests"] == 3
    assert result["total_tests"] == 3
    assert result["pass_rate"] == 1.0
    assert result["error_type"] is None


def test_partial_pass_classifies_error():
    report = {"summary": {"total": 4, "passed": 2}, "duration": 0.1}
    result = parse_pytest_report(
        report, stdout="", stderr="Traceback...\nAssertionError", timed_out=False, wall_time_seconds=0.1
    )
    assert result["pass_rate"] == 0.5
    assert result["error_type"] == "exception"


def test_timeout_reports_zero_pass_rate():
    result = parse_pytest_report(None, stdout="", stderr="", timed_out=True, wall_time_seconds=10.0)
    assert result["pass_rate"] == 0.0
    assert result["error_type"] == "timeout"


def test_missing_report_treated_as_infra_failure_not_crash():
    result = parse_pytest_report(
        None, stdout="", stderr="SyntaxError: invalid syntax", timed_out=False, wall_time_seconds=0.05
    )
    assert result["total_tests"] == 0
    assert result["error_type"] == "syntax_error"


def test_classify_error_priority_timeout_over_stderr_content():
    assert classify_error("SyntaxError: invalid syntax", timed_out=True) == "timeout"


def test_classify_error_syntax_vs_generic_exception():
    assert classify_error("SyntaxError: invalid syntax", timed_out=False) == "syntax_error"
    assert classify_error("Traceback (most recent call last):\nValueError", timed_out=False) == "exception"
    assert classify_error("", timed_out=False) is None
