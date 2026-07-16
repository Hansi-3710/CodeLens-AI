"""
Spins up an isolated, resource-limited Docker container to run untrusted
generated code. This is the security boundary of the whole platform —
generated code must NEVER execute in the FastAPI process.

Belongs to: backend/app/execution/
Phase: 5 (Execution Sandbox); hardened in the post-audit pass (see each
kwarg's comment below for the specific attack it closes off).

Note: this module needs a Docker daemon reachable at the socket mounted in
docker-compose.yml. It cannot be exercised in an environment with no Docker
daemon (e.g. this scaffold's CI sandbox) — see tests/test_docker_worker.py,
which mocks the `docker` client entirely and asserts the *call contract*
(network disabled, memory capped, timeout enforced, container removed),
not real execution. A `@pytest.mark.requires_docker` integration test is
provided for environments that do have Docker.
"""
from dataclasses import dataclass

import docker
from docker.errors import ContainerError, DockerException
from docker.types import Mount

from app.config import get_settings

# Hard cap on captured stdout/stderr: a solution that prints in a tight
# loop (accidentally or as a DoS attempt) shouldn't be able to balloon a
# TEXT column / the response body. This is independent of the sandbox's
# own resource limits — it protects the *caller*, not the container.
_MAX_CAPTURED_OUTPUT_BYTES = 64_000


def _truncate(text: str) -> str:
    if len(text) <= _MAX_CAPTURED_OUTPUT_BYTES:
        return text
    return text[:_MAX_CAPTURED_OUTPUT_BYTES] + "\n... [truncated: output exceeded 64KB]"


@dataclass
class SandboxRunResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


class DockerWorker:
    def __init__(self):
        self._settings = get_settings()
        self._client = None  # lazy: don't require a Docker daemon at import time

    def _get_client(self):
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def run(self, host_dir: str, command: list[str]) -> SandboxRunResult:
        """Runs `command` inside a disposable container with `host_dir`
        mounted at /workspace (needs to stay writable — pytest writes its
        JSON report there), executing as an unprivileged user with no
        network access, no Linux capabilities, no privilege escalation
        path, a capped process count, a read-only root filesystem, and a
        hard memory + wall-clock limit.
        """
        client = self._get_client()
        settings = self._settings
        try:
            container = client.containers.run(
                image=settings.DOCKER_SANDBOX_IMAGE,
                command=command,
                working_dir="/workspace",
                mounts=[Mount(target="/workspace", source=host_dir, type="bind", read_only=False)],
                network_disabled=True,  # no exfiltration, no calling out to attacker infra
                mem_limit=f"{settings.SANDBOX_MEMORY_LIMIT_MB}m",
                memswap_limit=f"{settings.SANDBOX_MEMORY_LIMIT_MB}m",  # = mem_limit: disables swap bypass
                nano_cpus=1_000_000_000,  # 1 CPU
                pids_limit=64,  # fork-bomb defense: a memory limit alone doesn't stop `while True: os.fork()`
                cap_drop=["ALL"],  # no Linux capabilities at all — the sandbox only needs to run Python
                security_opt=["no-new-privileges:true"],  # blocks setuid-binary privilege escalation
                read_only=True,  # root filesystem is immutable; only /workspace and /tmp (below) are writable
                tmpfs={"/tmp": "size=64m,noexec"},  # writable scratch space without letting written files be executed
                user="nobody",
                detach=True,
                remove=False,  # we remove manually after reading logs, see finally
            )
            try:
                result = container.wait(timeout=settings.SANDBOX_TIMEOUT_SECONDS)
                exit_code = result.get("StatusCode", -1)
                stdout = _truncate(container.logs(stdout=True, stderr=False).decode(errors="replace"))
                stderr = _truncate(container.logs(stdout=False, stderr=True).decode(errors="replace"))
                return SandboxRunResult(exit_code=exit_code, stdout=stdout, stderr=stderr, timed_out=False)
            except Exception:
                container.kill()
                return SandboxRunResult(exit_code=-1, stdout="", stderr="execution timed out", timed_out=True)
            finally:
                container.remove(force=True)
        except ContainerError as exc:
            return SandboxRunResult(exit_code=exc.exit_status, stdout="", stderr=str(exc), timed_out=False)
        except DockerException as exc:
            return SandboxRunResult(
                exit_code=-1, stdout="", stderr=f"sandbox infrastructure error: {exc}", timed_out=False
            )
