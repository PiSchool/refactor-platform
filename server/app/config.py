"""Layered configuration: .env secrets → config.yaml defaults → DB runtime overrides.

Secrets are read from the process environment only and are never persisted
or returned by the API (presence/absence only).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.results.archive_safety import ImportLimits

REPO_ROOT = Path(__file__).resolve().parents[2]


class Defaults(BaseModel):
    provider: str = "openrouter"
    model: str = "openrouter/free"
    task_timeout_seconds: int = 1800
    java_baseline_timeout_seconds: int = 900
    eval_tool_max_attempts: int = 3
    retention_runs_cap: int = 25


class ProviderConfig(BaseModel):
    """One OpenAI-compatible model provider.

    Adding a provider is a `config.yaml` entry, not a code change: the platform
    resolves the endpoint and key from the declared environment variables and
    hands the agent a provider-neutral `RP_PROVIDER_*` triple, which the agent
    adapter translates into whatever its CLI expects.
    """

    key: str
    name: str = ""
    base_url: str = ""
    api_key_env: str = ""
    base_url_env: str = ""
    #: provider publishes `GET /key` (credit balance); only OpenRouter does today
    credits: bool = False
    #: request formats this endpoint answers. Agent CLIs differ: Codex needs the
    #: OpenAI Responses API and Claude Code the Anthropic Messages API, so a
    #: pairing an endpoint cannot serve is refused instead of failing inside the
    #: agent with a message the operator has to decode.
    protocols: list[str] = Field(default_factory=lambda: ["chat_completions"])
    #: only where the Messages API does not sit under `base_url`
    anthropic_base_url: str = ""

    @property
    def label(self) -> str:
        return self.name or self.key

    def resolved_base_url(self) -> str:
        override = os.getenv(self.base_url_env, "").strip() if self.base_url_env else ""
        return override or self.base_url

    def speaks(self, protocol: str) -> bool:
        return protocol in self.protocols

    def resolved_anthropic_base_url(self) -> str:
        """Root the Anthropic Messages API is served from.

        Claude Code appends `/v1/messages` to what it is given, so the value is
        the endpoint root rather than the versioned path used for chat
        completions. Declared per provider where the two differ; otherwise the
        chat-completions URL with a trailing `/v1` removed.
        """
        if self.anthropic_base_url:
            return self.anthropic_base_url.rstrip("/")
        base = self.resolved_base_url().rstrip("/")
        return base[: -len("/v1")] if base.endswith("/v1") else base

    def resolved_api_key(self) -> str:
        return os.getenv(self.api_key_env, "").strip() if self.api_key_env else ""

    def requires_key(self) -> bool:
        return bool(self.api_key_env)


class RetrievalDefaults(BaseModel):
    """The models S2 searches with and how far each pipeline stage looks.

    These values are the only definition of the retrieval stack. `config.yaml`
    carries the same keys, and `test_retrieval_stack.py` fails if the two ever
    disagree, so "which model does S2 use" has one answer.
    """

    embedding_model: str = "hf.co/nomic-ai/nomic-embed-code-GGUF:Q4_K_M"
    embedding_dimension: int = 3584
    expansion_model: str = "qwen2.5-coder:7b-instruct"
    reranker_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    reranker_threads: int = Field(default=4, gt=0)
    vector_candidates: int = Field(default=50, gt=0)
    lexical_candidates: int = Field(default=50, gt=0)
    prefilter_candidates: int = Field(default=512, gt=0)
    fused_candidates: int = Field(default=40, gt=0)
    context_hits: int = Field(default=12, gt=0)
    context_char_limit: int = Field(default=24_000, gt=0)
    window_lines: int = Field(default=80, gt=0)
    overlap_lines: int = Field(default=20, ge=0)
    embed_num_ctx: int = Field(default=2048, gt=0)
    embed_num_batch: int = Field(default=2048, gt=0)
    embed_max_chars: int = Field(default=500, gt=0)


class EvidenceDefaults(BaseModel):
    view_max_bytes: int = Field(default=16 * 1024 * 1024, gt=0)
    download_max_bytes: int = Field(default=512 * 1024 * 1024, gt=0)
    json_max_bytes: int = Field(default=16 * 1024 * 1024, gt=0)
    stream_chunk_bytes: int = Field(default=64 * 1024, gt=0)


class Settings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: Path = REPO_ROOT / "data"
    plugins_dir: Path = REPO_ROOT / "plugins"
    database_url: str = ""
    defaults: Defaults = Defaults()
    providers: list[ProviderConfig] = Field(default_factory=list)
    retrieval: RetrievalDefaults = RetrievalDefaults()
    evidence: EvidenceDefaults = EvidenceDefaults()
    import_limits: ImportLimits = ImportLimits()

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

    def provider(self, key: str = "") -> ProviderConfig | None:
        wanted = (key or "").strip()
        for candidate in self.providers:
            if candidate.key == wanted:
                return candidate
        return None

    def active_provider(self) -> ProviderConfig:
        """The provider a run uses, from `RP_PROVIDER` or the configured default."""
        requested = os.getenv("RP_PROVIDER", "").strip() or self.defaults.provider
        return (
            self.provider(requested)
            or (self.providers[0] if self.providers else ProviderConfig(key=requested or "provider"))
        )

    # Secrets are read from the environment on demand and never persisted or
    # serialized; only their presence is ever reported.
    def provider_base_url(self) -> str:
        return self.active_provider().resolved_base_url()

    def provider_api_key(self) -> str:
        return self.active_provider().resolved_api_key()

    def provider_agent_env(self) -> dict[str, str]:
        """Provider access for an agent session.

        Every adapter receives the same three provider-neutral variables. The
        provider's own variable names are passed through as well, so an adapter
        that already speaks a vendor's convention keeps working unchanged.
        """
        provider = self.active_provider()
        base_url, api_key = provider.resolved_base_url(), provider.resolved_api_key()
        env = {
            "RP_PROVIDER": provider.key,
            "RP_PROVIDER_PROTOCOLS": ",".join(provider.protocols),
        }
        if base_url:
            env["RP_PROVIDER_BASE_URL"] = base_url
            # Where the endpoint also answers the Anthropic Messages API, its
            # root differs from the versioned chat-completions path.
            if provider.speaks("anthropic_messages"):
                env["RP_PROVIDER_ANTHROPIC_BASE_URL"] = provider.resolved_anthropic_base_url()
            if provider.base_url_env:
                env[provider.base_url_env] = base_url
        if api_key:
            env["RP_PROVIDER_API_KEY"] = api_key
            if provider.api_key_env:
                env[provider.api_key_env] = api_key
        return env


def config_file() -> Path | None:
    """The `config.yaml` this process reads, or None when it has none.

    The image copies it next to the server package, a checkout keeps it at the
    repository root, so both candidates are tried in order.
    """
    for candidate in (REPO_ROOT / "config.yaml", Path("config.yaml")):
        if candidate.is_file():
            return candidate
    return None


def _load_yaml() -> dict:
    candidate = config_file()
    if candidate is not None:
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
        providers=[ProviderConfig(**entry) for entry in raw.get("providers", [])],
        retrieval=RetrievalDefaults(**raw.get("retrieval", {})),
        evidence=EvidenceDefaults(
            **{
                **raw.get("evidence", {}),
                **{
                    key: int(value)
                    for key, env_name in {
                        "view_max_bytes": "RP_EVIDENCE_VIEW_MAX_BYTES",
                        "download_max_bytes": "RP_EVIDENCE_DOWNLOAD_MAX_BYTES",
                        "json_max_bytes": "RP_EVIDENCE_JSON_MAX_BYTES",
                        "stream_chunk_bytes": "RP_EVIDENCE_STREAM_CHUNK_BYTES",
                    }.items()
                    if (value := os.getenv(env_name))
                },
            }
        ),
        import_limits=ImportLimits.from_env(),
    )
    if not settings.providers:
        # A deployment with no declared provider could not run anything, and a
        # silent empty registry would surface as an unexplained missing key.
        settings.providers = [
            ProviderConfig(
                key="openrouter",
                name="OpenRouter",
                base_url="https://openrouter.ai/api/v1",
                api_key_env="OPENROUTER_API_KEY",
                base_url_env="OPENROUTER_BASE_URL",
                credits=True,
                protocols=["chat_completions", "responses", "anthropic_messages"],
                anthropic_base_url="https://openrouter.ai/api",
            )
        ]
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings


def secret_presence() -> dict[str, str]:
    """Report which secrets are configured without exposing values."""
    settings = get_settings()
    presence = {
        f"{provider.key}Key": "present" if provider.resolved_api_key() else "absent"
        for provider in settings.providers
        if provider.requires_key()
    }
    presence["providerKey"] = (
        "present" if settings.provider_api_key() else "absent"
    )
    presence["copilotToken"] = (
        "present" if os.getenv("COPILOT_GITHUB_TOKEN", "").strip() else "absent"
    )
    return presence


def provider_inventory() -> list[dict]:
    """Configured providers for the API: identity and readiness, never a key."""
    settings = get_settings()
    active = settings.active_provider().key
    return [
        {
            "key": provider.key,
            "name": provider.label,
            "baseUrl": provider.resolved_base_url(),
            "apiKeyEnv": provider.api_key_env,
            "keyState": (
                "not-required" if not provider.requires_key()
                else "present" if provider.resolved_api_key()
                else "absent"
            ),
            "credits": provider.credits,
            "active": provider.key == active,
        }
        for provider in settings.providers
    ]
