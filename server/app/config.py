"""Layered configuration: .env secrets → config.yaml defaults → DB runtime overrides.

Secrets are read from the process environment only and are never persisted
or returned by the API (presence/absence only).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[2]


class Defaults(BaseModel):
    model: str = "openrouter/free"
    task_timeout_seconds: int = 1800
    eval_tool_max_attempts: int = 3
    retention_runs_cap: int = 25


class Settings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: Path = REPO_ROOT / "data"
    plugins_dir: Path = REPO_ROOT / "plugins"
    database_url: str = ""
    defaults: Defaults = Defaults()

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def mirrors_dir(self) -> Path:
        return self.data_dir / "mirrors"

    @property
    def prompt_overrides_dir(self) -> Path:
        """Operator-edited prompt templates. Kept in the data volume so they
        survive image rebuilds, unlike the plugin's shipped defaults."""
        return self.data_dir / "prompt-overrides"

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.data_dir / 'platform.db'}"

    # Secrets are read from the environment on demand and never persisted or
    # serialized; only their presence is ever reported.
    def provider_base_url(self) -> str:
        return os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    def provider_api_key(self) -> str:
        return os.getenv("OPENROUTER_API_KEY", "")


def _load_yaml() -> dict:
    for candidate in (REPO_ROOT / "config.yaml", Path("config.yaml")):
        if candidate.is_file():
            return yaml.safe_load(candidate.read_text()) or {}
    return {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    raw = _load_yaml()
    server = raw.get("server", {})
    settings = Settings(
        host=server.get("host", "0.0.0.0"),
        port=int(server.get("port", 8000)),
        data_dir=Path(os.getenv("RP_DATA_DIR", str(REPO_ROOT / "data"))),
        plugins_dir=Path(os.getenv("RP_PLUGINS_DIR", str(REPO_ROOT / "plugins"))),
        database_url=os.getenv("DATABASE_URL", ""),
        defaults=Defaults(**raw.get("defaults", {})),
    )
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings


def secret_presence() -> dict[str, str]:
    """Report which secrets are configured without exposing values."""
    return {
        "openrouterKey": "present" if os.getenv("OPENROUTER_API_KEY", "").strip() else "absent",
        "copilotToken": "present" if os.getenv("COPILOT_GITHUB_TOKEN", "").strip() else "absent",
    }
