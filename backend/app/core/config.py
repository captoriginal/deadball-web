import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean from the environment with sensible defaults."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Deadball Web API"))
    api_prefix: str = field(default_factory=lambda: os.getenv("API_PREFIX", "/api"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///deadball_dev.db"))
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", False))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance sourced from environment variables."""
    return Settings()
