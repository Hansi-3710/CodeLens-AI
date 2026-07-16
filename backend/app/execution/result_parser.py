"""
Parses raw sandbox output (pytest's --json-report JSON, plus stdout/stderr)
into a structured dict matching the ExecutionResult schema.

Belongs to: backend/app/execution/
Phase: 5 (Execution Sandbox)
"""


def classify_error(stderr: str, timed_out: bool) -> str | None:
    if timed_out:
        return "timeout"
    if "SyntaxError" in stderr:
        return "syntax_error"
    if "MemoryError" in stderr:
        return "memory_error"
    if any(exc in stderr for exc in ("Traceback", "Error")):
        return "exception"
    return None


def parse_pytest_report(
    report_json: dict | None,
    stdout: str,
    stderr: str,
    timed_out: bool,
    wall_time_seconds: float,
) -> dict:
    if timed_out or report_json is None:
        return {
            "passed_tests": 0,
            "total_tests": 0,
            "pass_rate": 0.0,
            "runtime_seconds": wall_time_seconds,
            "memory_mb": None,
            "stdout": stdout,
            "stderr": stderr,
            "error_type": classify_error(stderr, timed_out),
        }

    summary = report_json.get("summary", {})
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)

    return {
        "passed_tests": passed,
        "total_tests": total,
        "pass_rate": (passed / total) if total else 0.0,
        "runtime_seconds": report_json.get("duration", wall_time_seconds),
        "memory_mb": None,  # requires a memory-profiling wrapper inside the sandbox image; not in Phase 5 scope
        "stdout": stdout,
        "stderr": stderr,
        "error_type": None if passed == total else classify_error(stderr, timed_out),
    }
