"""
Builds the test harness (submitted code + reference tests) that gets
mounted into the sandbox container, and invokes DockerWorker to execute it.

Belongs to: backend/app/execution/
Phase: 5 (Execution Sandbox)
"""
import json
import os
import stat
import tempfile
import time
from pathlib import Path

from app.execution.docker_worker import DockerWorker
from app.execution.result_parser import parse_pytest_report

_TEST_FILE_TEMPLATE = '''"""Auto-generated harness — DO NOT EDIT. See sandbox_runner.py."""
import json
from solution import *  # noqa: F401,F403 - generated solution under test

{test_functions}
'''


def render_test_file(reference_tests: list[dict]) -> str:
    """Turns [{"input": [...], "expected_output": ...}] into pytest
    functions. Each test asserts the named entry point's return value.

    Kept intentionally simple (assert-equality only) for Phase 5; richer
    matchers (approx-equality for floats, exception-expected tests) are a
    natural Phase 6+ extension once real problem sets are wired in.
    """
    functions = []
    for i, test in enumerate(reference_tests):
        call = test["call"]  # e.g. "reverse_linked_list([1, 2, 3])"
        expected = repr(test["expected_output"])
        functions.append(
            f"def test_case_{i}():\n    assert {call} == {expected}\n"
        )
    return _TEST_FILE_TEMPLATE.format(test_functions="\n\n".join(functions))


def run_solution_in_sandbox(code: str, reference_tests: list[dict]) -> dict:
    """Returns a dict matching ExecutionResult's fields."""
    worker = DockerWorker()

    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        (workspace / "solution.py").write_text(code)
        (workspace / "test_solution.py").write_text(render_test_file(reference_tests))

        # tempfile.TemporaryDirectory() defaults to 0700, owned by whatever
        # user runs this process (typically root inside the backend
        # container). The sandbox container runs as the unprivileged
        # 'nobody' user (see docker_worker.py) and needs to write
        # report.json back into this same directory — without opening up
        # permissions here, that write fails with EACCES regardless of
        # Docker's UID namespace mapping. The directory is destroyed the
        # moment this `with` block exits, so the broader permission window
        # is scoped to a single sandbox run, not a standing risk.
        os.chmod(workspace, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        start = time.monotonic()
        result = worker.run(
            host_dir=str(workspace),
            command=[
                "pytest", "test_solution.py",
                "--json-report", "--json-report-file=report.json",
                "-q",
            ],
        )
        wall_time = time.monotonic() - start

        report_path = workspace / "report.json"
        report_json = json.loads(report_path.read_text()) if report_path.exists() else None

        return parse_pytest_report(
            report_json=report_json,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
            wall_time_seconds=wall_time,
        )
