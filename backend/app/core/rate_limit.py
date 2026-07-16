"""
Rate limiting — protects auth endpoints from brute-force credential
stuffing and /generate from being used to rack up unbounded LLM API spend
on someone else's account (or a runaway frontend retry loop).

Belongs to: backend/app/core/
Phase: hardening pass (post-audit)

Limits are per-client-IP via slowapi (in-memory by default). For a
multi-instance production deployment, swap the default in-memory storage
for a shared Redis backend (slowapi supports this via `storage_uri=`) so
limits are enforced across instances, not per-process.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
