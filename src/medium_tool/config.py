"""Configuration and API key management."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    openai_api_key: str = ""
    unsplash_access_key: str = ""
    medium_token: str = ""

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_unsplash(self) -> bool:
        return bool(self.unsplash_access_key)

    @property
    def has_medium(self) -> bool:
        return bool(self.medium_token)


def load_config(env_path: Path | None = None) -> Config:
    """Load config from .env file and environment variables."""
    if env_path and env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    return Config(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        unsplash_access_key=os.getenv("UNSPLASH_ACCESS_KEY", "").strip(),
        medium_token=os.getenv("MEDIUM_TOKEN", "").strip(),
    )


def validate_config(config: Config, need_publish: bool = False) -> list[str]:
    """Return list of missing key errors. Empty list means all good."""
    errors = []
    if need_publish and not config.has_medium:
        errors.append("MEDIUM_TOKEN is required for publishing")
    return errors
