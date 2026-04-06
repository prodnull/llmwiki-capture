"""Configuration for llmwiki-capture."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

import yaml


def _load_yaml_config() -> dict[str, Any]:
    """Load config.yml if it exists, return empty dict otherwise."""
    for candidate in [Path("config.yml"), Path("config.yaml")]:
        if candidate.exists():
            with open(candidate) as f:
                return yaml.safe_load(f) or {}
    return {}


def _resolve_wiki_inbox(wiki_path: str, wiki_name: str | None) -> Path:
    """Resolve the inbox path within an llm-wiki structure."""
    base = Path(wiki_path).expanduser()
    if wiki_name:
        return base / wiki_name / "inbox"
    return base / "inbox"


class Config:
    """App configuration. Env vars take precedence over config.yml."""

    def __init__(self) -> None:
        file_cfg = _load_yaml_config()

        self.token: str = os.environ.get("CAPTURE_TOKEN", file_cfg.get("token", ""))
        self.port: int = int(os.environ.get("CAPTURE_PORT", file_cfg.get("port", 7199)))
        self.host: str = os.environ.get("CAPTURE_HOST", file_cfg.get("host", "0.0.0.0"))
        wiki_path: str = os.environ.get(
            "WIKI_PATH", file_cfg.get("wiki_path", "~/wiki")
        )
        wiki_name: str | None = os.environ.get(
            "CAPTURE_WIKI_NAME", file_cfg.get("wiki_name")
        )
        self.inbox_path: Path = _resolve_wiki_inbox(wiki_path, wiki_name)
        self.rate_limit: int = int(
            os.environ.get("CAPTURE_RATE_LIMIT", file_cfg.get("rate_limit", 60))
        )

        if not self.token:
            self.token = secrets.token_urlsafe(32)
            print(f"Generated token (save this): {self.token}")

    def ensure_inbox(self) -> None:
        """Create inbox directory if it doesn't exist."""
        self.inbox_path.mkdir(parents=True, exist_ok=True)
