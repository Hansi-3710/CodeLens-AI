# The execution sandbox image — built separately from the backend API image.
# Intentionally minimal: only what's needed to run a submitted Python
# solution against pytest. No network access at runtime (docker_worker.py
# passes network_disabled=True regardless, this is defense in depth).
FROM python:3.12-slim

RUN pip install --no-cache-dir pytest==8.3.* pytest-json-report==1.5.*

# Unprivileged user the container runs as (docker_worker.py sets user="nobody"
# explicitly too; this just ensures the image itself doesn't assume root).
RUN useradd --no-create-home --shell /usr/sbin/nologin sandboxrunner

WORKDIR /workspace
