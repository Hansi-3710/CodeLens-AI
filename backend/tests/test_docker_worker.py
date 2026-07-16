"""
Tests DockerWorker's *call contract* (the security-relevant kwargs it
passes to the Docker SDK) using a mocked docker client — this environment
has no Docker daemon, so these tests assert intent, not real execution.

A true integration test (marked requires_docker, skipped automatically
when no daemon is reachable) is included for environments that do have
Docker — e.g. CI or a developer's machine.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.execution.docker_worker import DockerWorker


def test_run_enforces_network_disabled_and_memory_limit():
    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [b"ok", b""]

    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container

    worker = DockerWorker()
    worker._client = mock_client  # inject the mock instead of docker.from_env()

    result = worker.run(host_dir="/tmp/fake", command=["pytest"])

    _, kwargs = mock_client.containers.run.call_args
    assert kwargs["network_disabled"] is True
    assert "m" in kwargs["mem_limit"]
    assert kwargs["user"] == "nobody"
    assert result.exit_code == 0
    mock_container.remove.assert_called_once_with(force=True)


def test_run_enforces_network_disabled_and_memory_limit():
    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [b"ok", b""]

    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container

    worker = DockerWorker()
    worker._client = mock_client  # inject the mock instead of docker.from_env()

    result = worker.run(host_dir="/tmp/fake", command=["pytest"])

    _, kwargs = mock_client.containers.run.call_args
    assert kwargs["network_disabled"] is True
    assert "m" in kwargs["mem_limit"]
    assert kwargs["user"] == "nobody"
    assert result.exit_code == 0
    mock_container.remove.assert_called_once_with(force=True)


def test_run_enforces_full_hardening_contract():
    """Every kwarg here closes a specific, named attack — see docker_worker.py's
    inline comments for which one. This test exists so a future edit that
    accidentally drops one of them (e.g. someone "simplifying" the
    containers.run() call) fails CI instead of silently reopening a hole."""
    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [b"", b""]

    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container

    worker = DockerWorker()
    worker._client = mock_client
    worker.run(host_dir="/tmp/fake", command=["pytest"])

    _, kwargs = mock_client.containers.run.call_args
    assert kwargs["cap_drop"] == ["ALL"]
    assert kwargs["security_opt"] == ["no-new-privileges:true"]
    assert kwargs["pids_limit"] == 64
    assert kwargs["read_only"] is True
    assert "/tmp" in kwargs["tmpfs"]
    assert kwargs["memswap_limit"] == kwargs["mem_limit"]  # swap disabled: memory limit can't be bypassed via swap


def test_captured_output_is_truncated_not_unbounded():
    from app.execution.docker_worker import _truncate

    huge = "x" * 200_000
    truncated = _truncate(huge)
    assert len(truncated) < len(huge)
    assert "truncated" in truncated


def test_run_kills_and_reports_timeout_on_wait_exception():
    mock_container = MagicMock()
    mock_container.wait.side_effect = TimeoutError("timed out")

    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container

    worker = DockerWorker()
    worker._client = mock_client

    result = worker.run(host_dir="/tmp/fake", command=["pytest"])

    mock_container.kill.assert_called_once()
    assert result.timed_out is True


def _docker_daemon_available() -> bool:
    try:
        import docker
        docker.from_env().ping()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _docker_daemon_available(), reason="requires a reachable Docker daemon")
@pytest.mark.requires_docker
def test_real_sandbox_executes_trivial_solution():
    """Real integration test — build ./sandbox first: see sandbox/README.md."""
    from app.execution.sandbox_runner import run_solution_in_sandbox

    code = "def add(a, b):\n    return a + b\n"
    tests = [{"call": "add(2, 3)", "expected_output": 5}]
    result = run_solution_in_sandbox(code, tests)
    assert result["pass_rate"] == 1.0
