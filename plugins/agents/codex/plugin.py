"""OpenAI Codex CLI adapter (verified against codex-cli 0.145.0).

Codex is pointed at the provider the platform selected. Its custom-provider
support speaks the OpenAI Responses API, so an endpoint that only implements
chat completions cannot drive this adapter — the run fails with that reason
rather than falling back to a different provider.

The platform owns the PTY; this adapter writes the private CODEX_HOME, builds
the launch command, and reads the normalized event file written by `run.py`.
Imports ONLY from app.catalog.sdk.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

# A plugin's own modules are imported relative to it. Bare `import events`
# would collide with the other adapters, which ship a module of that name too.
from . import events as events_mod


def _toml_key(key: str) -> str:
    plain = all(ch.isalnum() or ch in "_-" for ch in key)
    return key if key and plain else json.dumps(key)


def _toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    return json.dumps(str(value))


def _toml_table(header: str, values: dict) -> str:
    lines = [f"[{header}]"]
    for key, value in values.items():
        if isinstance(value, dict):
            continue
        lines.append(f"{_toml_key(key)} = {_toml_value(value)}")
    for key, value in values.items():
        if isinstance(value, dict):
            lines.append("")
            lines.append(_toml_table(f"{header}.{_toml_key(key)}", value))
    return "\n".join(lines)


class Plugin(AgentPlugin):
    capabilities = {"lsp": False, "subagents": False, "eval_tool": True, "retrieval": True}
    #: Codex's custom-provider support speaks the OpenAI Responses API; a
    #: provider that answers only chat completions is refused before the run.
    wire = "responses"
    models: list[str] = []
    _requested_model = ""

    def _home(self, session: SessionCtx) -> Path:
        return session.config_dir / ".codex"

    def _events_file(self, session: SessionCtx) -> Path:
        return session.config_dir / "events.jsonl"

    def prepare(self, session: SessionCtx) -> None:
        self._requested_model = session.model
        home = self._home(session)
        home.mkdir(parents=True, exist_ok=True)
        base_url = session.requested_env.get("RP_PROVIDER_BASE_URL", "").strip()
        if not base_url:
            provider = session.requested_env.get("RP_PROVIDER", "provider").strip() or "provider"
            raise RuntimeError(
                f"no base URL configured for provider {provider!r}; "
                "set it in config.yaml or its base-URL environment variable"
            )
        blocks = [
            f"model = {_toml_value(session.model)}",
            'model_provider = "platform"',
            'approval_policy = "never"',
            'sandbox_mode = "danger-full-access"',
            "",
            _toml_table("model_providers.platform", {
                "name": "Platform provider",
                "base_url": base_url,
                "env_key": "RP_PROVIDER_API_KEY",
                "wire_api": "responses",
                "request_max_retries": 2,
                "stream_max_retries": 2,
            }),
        ]
        for name, spec in ((session.mcp_config or {}).get("mcpServers", {}) or {}).items():
            if spec.get("disabled"):
                continue
            table = {
                "command": spec.get("command", ""),
                "args": list(spec.get("args", [])),
                "startup_timeout_sec": 60,
                "tool_timeout_sec": int(spec.get("timeout", 600000)) // 1000,
            }
            if spec.get("env"):
                table["env"] = dict(spec["env"])
            blocks += ["", _toml_table(f"mcp_servers.{json.dumps(str(name))}", table)]
        (home / "config.toml").write_text("\n".join(blocks) + "\n", encoding="utf-8")

    def _codex_argv(self, session: SessionCtx, resume: bool) -> list[str]:
        argv = ["codex", "exec"]
        if resume:
            argv += ["resume", "--last"]
        argv += [
            "--json", "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            "-C", str(session.workspace),
            "-m", session.model,
            "-o", str(session.config_dir / "last-message.txt"),
        ]
        return argv

    def _wrapped(self, session: SessionCtx, prompt_path: Path, resume: bool) -> CommandSpec:
        argv = [
            sys.executable, str(Path(__file__).parent / "run.py"),
            "--events", str(self._events_file(session)),
            "--prompt", str(prompt_path),
            "--model", session.model,
            "--", *self._codex_argv(session, resume),
        ]
        return CommandSpec(argv=argv, env=self._env(session), cwd=session.workspace)

    def command(self, session: SessionCtx) -> CommandSpec:
        return self._wrapped(session, session.prompt_path, resume=False)

    def resume_command(self, session: SessionCtx, prompt_path: Path) -> CommandSpec:
        return self._wrapped(session, prompt_path, resume=True)

    def _env(self, session: SessionCtx) -> dict[str, str]:
        env = dict(session.requested_env)
        key = env.get("RP_PROVIDER_API_KEY", "").strip()
        if not key:
            provider = env.get("RP_PROVIDER", "provider").strip() or "provider"
            raise RuntimeError(
                f"no API key configured for provider {provider!r}; "
                "set its API-key environment variable in .env"
            )
        env["CODEX_HOME"] = str(self._home(session))
        # Codex would otherwise pick up a stray key for its built-in provider.
        env["OPENAI_API_KEY"] = key
        return env

    def events_path(self, session: SessionCtx) -> Path | None:
        path = self._events_file(session)
        return path if path.is_file() else None

    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo:
        parsed = events_mod.parse(events_path, terminal_log_path, self._requested_model)
        return SessionInfo(
            tokens_input=parsed["tokens_input"],
            tokens_output=parsed["tokens_output"],
            tokens_cache_read=parsed["tokens_cache_read"],
            tokens_reasoning=parsed["tokens_reasoning"],
            context_tokens=parsed["context_tokens"],
            model=parsed["model"],
            response_text=parsed["response_text"],
            readable_transcript=parsed["readable_transcript"],
            flags=set(parsed["flags"]),
            eval_tool_invocations=parsed["eval_tool_invocations"],
            retrieval_invocations=parsed["retrieval_invocations"],
        )
