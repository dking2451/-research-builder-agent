from functools import lru_cache
from getpass import getuser
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load backend/.env (not cwd-relative), so uvicorn works from any directory.
_BACKEND_DIR = Path(__file__).resolve().parent.parent


def _default_database_url() -> str:
    # Homebrew Postgres on macOS uses the login name as the DB superuser, not "postgres".
    # Set DATABASE_URL in .env for Docker/Linux (e.g. postgres:postgres@...).
    return f"postgresql+psycopg://{getuser()}@localhost:5432/research_builder"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(default_factory=_default_database_url)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"
    default_user_email: str = "owner@local.test"
    # If true (or missing OPENAI_API_KEY), agent runs return a deterministic stub envelope.
    use_stub_agent: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
