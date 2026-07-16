# Sandbox image

Build with:

    docker build -t llm-code-intel-sandbox:latest ./sandbox

This must match `DOCKER_SANDBOX_IMAGE` in `app/config.py` / `.env`.
`docker-compose.yml` does not build this automatically (it's built
on-demand, not part of the always-running services) — build it once
before the first `/solutions/{id}/execute` call.
