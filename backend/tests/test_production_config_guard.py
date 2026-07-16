"""Proves the production startup guard actually fires — not just that it's
wired without erroring."""
import pytest

from app.config import Settings


def test_production_with_default_secret_key_refuses_to_start():
    settings = Settings(ENVIRONMENT="production", SECRET_KEY="change-me-in-production",
                         DATABASE_URL="postgresql://user:pass@real-host:5432/proddb",
                         ALLOWED_ORIGINS=["https://real-app.vercel.app"])
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        settings.validate_for_production()


def test_production_with_localhost_database_refuses_to_start():
    settings = Settings(ENVIRONMENT="production", SECRET_KEY="a-real-random-secret-key-value",
                         DATABASE_URL="postgresql+psycopg://postgres:postgres@db:5432/llm_code_intel",
                         ALLOWED_ORIGINS=["https://real-app.vercel.app"])
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        settings.validate_for_production()


def test_production_with_default_cors_origin_refuses_to_start():
    settings = Settings(ENVIRONMENT="production", SECRET_KEY="a-real-random-secret-key-value",
                         DATABASE_URL="postgresql://user:pass@real-host:5432/proddb")
    with pytest.raises(RuntimeError, match="ALLOWED_ORIGINS"):
        settings.validate_for_production()


def test_production_with_everything_configured_starts_cleanly():
    settings = Settings(ENVIRONMENT="production", SECRET_KEY="a-real-random-secret-key-value",
                         DATABASE_URL="postgresql://user:pass@real-host:5432/proddb",
                         ALLOWED_ORIGINS=["https://real-app.vercel.app"])
    settings.validate_for_production()  # should not raise


def test_development_environment_is_never_blocked():
    settings = Settings(ENVIRONMENT="development")
    settings.validate_for_production()  # should not raise, regardless of defaults


def test_allowed_origins_accepts_comma_separated_string():
    """What you'd actually paste into Render/Vercel's env var UI — a plain
    comma-separated string, not a JSON array."""
    settings = Settings(ALLOWED_ORIGINS="https://a.vercel.app,https://b.vercel.app")
    assert settings.ALLOWED_ORIGINS == ["https://a.vercel.app", "https://b.vercel.app"]


def test_allowed_origins_still_accepts_json_array_string():
    settings = Settings(ALLOWED_ORIGINS='["https://a.vercel.app"]')
    assert settings.ALLOWED_ORIGINS == ["https://a.vercel.app"]
