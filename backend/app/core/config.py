import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean from the environment with sensible defaults."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: List[str] | None = None) -> List[str]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default or []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class Settings:
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Deadball Web API"))
    api_prefix: str = field(default_factory=lambda: os.getenv("API_PREFIX", "/api"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///deadball_dev.db"))
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", False))
    cors_origins: List[str] = field(default_factory=lambda: _env_list("CORS_ORIGINS", ["http://localhost:5173"]))
    allow_generator_network: bool = field(default_factory=lambda: _env_bool("ALLOW_GENERATOR_NETWORK", True))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance sourced from environment variables."""
    return Settings()
