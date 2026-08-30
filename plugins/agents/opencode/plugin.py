"""opencode adapter (verified against opencode 1.18.5).

opencode reaches a model through a provider declared in its own configuration
file. The platform writes that file per session: the endpoint and key it resolved
appear as an OpenAI-compatible provider named `platform`, and the model is then
addressed as `platform/<model>`, so no vendor is named to the agent.

The platform owns the PTY; this adapter writes the configuration, builds the
launch command, and reads the normalized event file written by `run.py`.
Imports ONLY from app.catalog.sdk.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

# A plugin's own modules are imported relative to it. Bare `import events` would
# collide with the other adapters, which ship a module of that name too.
from . import events as events_mod

#: opencode addresses a model as `<providerId>/<modelId>`; this is the provider
#: id the platform declares for whichever endpoint it resolved.
PROVIDER_ID = "platform"


class Plugin(AgentPlugin):
    capabilities = {"lsp": False, "subagents": True, "eval_tool": True, "retrieval": True}
    models: list[str] = []
    _requested_model = ""

    # opencode keeps its state under the session's private home, so nothing of
    # its own lands in the captured diff.
    workspace_artifacts: tuple[str, ...] = ()

    def _config_file(self, session: SessionCtx) -> Path:
        return session.config_dir / "opencode.json"

    def _events_file(self, session: SessionCtx) -> Path:
        return session.config_dir / "events.jsonl"

    def prepare(self, session: SessionCtx) -> None:
        self._requested_model = session.model
        base_url = session.requested_env.get("RP_PROVIDER_BASE_URL", "").strip()
        api_key = session.requested_env.get("RP_PROVIDER_API_KEY", "").strip()
        provider = session.requested_env.get("RP_PROVIDER", "provider").strip() or "provider"
        if not base_url:
            raise RuntimeError(
                f"no base URL configured for provider {provider!r}; "
                "set it in config.yaml or its base-URL environment variable"
            )
        if not api_key:
            raise RuntimeError(
                f"no API key configured for provider {provider!r}; "
                "set its API-key environment variable in .env"
            )
        config: dict = {
            "$schema": "https://opencode.ai/config.json",
            "provider": {
                PROVIDER_ID: {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": provider,
                    "options": {"baseURL": base_url, "apiKey": api_key},
                    "models": {session.model: {"name": session.model}},
                }
            },
            # A batch run has no operator to answer a permission prompt; the
            # launch also passes --auto, and this keeps the file self-describing.
            "autoupdate": False,
            "share": "disabled",
        }
        servers = {
            name: {
                "type": "local",
                "command": [spec.get("command", ""), *list(spec.get("args", []))],
                "environment": dict(spec.get("env") or {}),
                "enabled": True,
            }
            for name, spec in ((session.mcp_config or {}).get("mcpServers", {}) or {}).items()
            if not spec.get("disabled")
        }
        if servers:
            config["mcp"] = servers
        self._config_file(session).write_text(
            json.dumps(config, indent=2) + "\n", encoding="utf-8")

    def _opencode_argv(self, session: SessionCtx, resume: bool) -> list[str]:
        argv = [
            "opencode", "run",
            "--format", "json",
            "--auto",                       # no operator is present to approve a tool
            "--model", f"{PROVIDER_ID}/{session.model}",
            "--dir", str(session.workspace),
        ]
        if resume:
            argv.append("--continue")
        return argv

    def _wrapped(self, session: SessionCtx, prompt_path: Path, resume: bool) -> CommandSpec:
        argv = [
            sys.executable, str(Path(__file__).parent / "run.py"),
            "--events", str(self._events_file(session)),
            "--prompt", str(prompt_path),
            "--model", session.model,
            "--", *self._opencode_argv(session, resume),
        ]
        return CommandSpec(argv=argv, env=self._env(session), cwd=session.workspace)

    def command(self, session: SessionCtx) -> CommandSpec:
        return self._wrapped(session, session.prompt_path, resume=False)

    def resume_command(self, session: SessionCtx, prompt_path: Path) -> CommandSpec:
        return self._wrapped(session, prompt_path, resume=True)

    def _env(self, session: SessionCtx) -> dict[str, str]:
        env = dict(session.requested_env)
        home = str(session.config_dir)
        env["OPENCODE_CONFIG"] = str(self._config_file(session))
        env["OPENCODE_DISABLE_AUTOUPDATE"] = "1"
        # Its cache, credentials and session store go under the session's own
        # home, so two tasks cannot read each other's state.
        env["XDG_CONFIG_HOME"] = f"{home}/.config"
        env["XDG_DATA_HOME"] = f"{home}/.local/share"
        env["XDG_CACHE_HOME"] = f"{home}/.cache"
        env["XDG_STATE_HOME"] = f"{home}/.local/state"
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
