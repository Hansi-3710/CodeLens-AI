"""
Centralized application configuration, loaded from environment variables.

Belongs to: backend/app/
"""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "LLM Code Intelligence Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/llm_code_intel"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LLM providers
    OPENAI_API_KEY: str | None = None
    HUGGINGFACE_API_TOKEN: str | None = None

    # Execution sandbox
    DOCKER_SANDBOX_IMAGE: str = "llm-code-intel-sandbox:latest"
    SANDBOX_TIMEOUT_SECONDS: int = 10
    SANDBOX_MEMORY_LIMIT_MB: int = 256

    # CORS — accepts either a JSON array ('["https://a.com","https://b.com"]')
    # or, more realistically for pasting into a Render/Vercel env var field,
    # a plain comma-separated string ('https://a.com,https://b.com').
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_comma_separated(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                import json
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    def validate_for_production(self) -> None:
        """Called once at startup (see main.py). Fails loudly rather than
        silently shipping an insecure default — the audit flagged
        SECRET_KEY's default as a Critical Issue precisely because nothing
        previously stopped it from being used as-is in production.
        """
        if self.ENVIRONMENT != "production":
            return
        problems = []
        if self.SECRET_KEY == "change-me-in-production":
            problems.append(
                "SECRET_KEY is still the insecure default. Set a real random value "
                "(Render's render.yaml already does this via generateValue: true)."
            )
        if "localhost" in self.DATABASE_URL or "db:5432" in self.DATABASE_URL:
            problems.append("DATABASE_URL still points at a local/dev database.")
        if self.ALLOWED_ORIGINS == ["http://localhost:5173"]:
            problems.append(
                "ALLOWED_ORIGINS is still the localhost default — set it to your real "
                "deployed frontend URL (e.g. https://your-app.vercel.app) or CORS will "
                "silently reject the real frontend's requests."
            )
        if problems:
            raise RuntimeError(
                "Refusing to start with ENVIRONMENT=production and insecure defaults:\n- "
                + "\n- ".join(problems)
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
