"""Proves the rate limiter actually rejects excess requests, not just that
it's wired without erroring."""


def test_login_is_rate_limited_after_repeated_attempts(client, auth_headers):
    # auth_headers fixture already performed one login; login limit is 10/minute.
    responses = [
        client.post("/auth/login", data={"username": "researcher@example.com", "password": "wrong"})
        for _ in range(12)
    ]
    statuses = [r.status_code for r in responses]
    assert 429 in statuses, "expected at least one request to be rate-limited"
    # The ones before the limit trips should be normal auth failures (401), not something else.
    assert all(s in (401, 429) for s in statuses)


def test_register_is_rate_limited_after_repeated_attempts(client):
    responses = [
        client.post("/auth/register", json={"email": f"spam{i}@example.com", "password": "password123"})
        for i in range(8)
    ]
    statuses = [r.status_code for r in responses]
    assert 429 in statuses
