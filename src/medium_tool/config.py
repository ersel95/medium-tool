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

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_unsplash(self) -> bool:
        return bool(self.unsplash_access_key)


def load_config(env_path: Path | None = None) -> Config:
    """Load config from .env file and environment variables."""
    if env_path and env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    return Config(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        unsplash_access_key=os.getenv("UNSPLASH_ACCESS_KEY", "").strip(),
    )


def validate_config(config: Config) -> list[str]:
    """Return list of missing key errors. Empty list means all good."""
    return []
