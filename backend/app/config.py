import os
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_frozen() -> bool:
    """Check if we are running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def _default_database_url() -> str:
    """Return the default DATABASE_URL based on runtime mode."""
    if _is_frozen():
        # EXE mode: use SQLite in the same directory as the executable
        exe_dir = os.path.dirname(sys.executable)
        db_path = os.path.join(exe_dir, "knowyourrate.db")
        return f"sqlite+aiosqlite:///{db_path}"
    return "postgresql+asyncpg://postgres:postgres@localhost:5432/knowyourrate"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    DATABASE_URL: str = _default_database_url()
    ENCRYPTION_SECRET: str = "change-me-in-production-must-be-32-bytes!"
    YOUTUBE_API_KEY: str | None = None

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def is_frozen(self) -> bool:
        return _is_frozen()


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
