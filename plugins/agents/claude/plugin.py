"""Claude Code adapter (verified against Claude Code 2.1.211).

Claude Code sends Anthropic Messages requests, so it runs against any endpoint
that answers that API. The platform declares per provider which request formats
it answers and refuses the pairing otherwise, naming the protocol, instead of
letting the agent die on a `404` the operator has to decode.

Claude Code appends `/v1/messages` to the base URL it is given, so the value it
receives is the endpoint root rather than the versioned chat-completions path;
`RP_PROVIDER_ANTHROPIC_BASE_URL` carries it.

The platform owns the PTY; this adapter writes the private settings directory,
builds the launch command, and reads the normalized event file written by
`run.py`. Imports ONLY from app.catalog.sdk.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

# A plugin's own modules are imported relative to it. Bare `import events` would
# collide with the other adapters, which ship a module of that name too.
from . import events as events_mod


class Plugin(AgentPlugin):
    capabilities = {"lsp": False, "subagents": True, "eval_tool": True, "retrieval": True}
    #: request format this CLI sends; the provider must answer it
    wire = "anthropic_messages"
    models: list[str] = []
    _requested_model = ""

    def _home(self, session: SessionCtx) -> Path:
        return session.config_dir / ".claude"

    def _events_file(self, session: SessionCtx) -> Path:
        return session.config_dir / "events.jsonl"

    def _mcp_file(self, session: SessionCtx) -> Path:
        return session.config_dir / "claude-mcp.json"

    # Nothing of Claude Code's own lands in the workspace: its home, settings and
    # per-project memory are all under the session's private config directory,
    # so the captured diff is the agent's change alone.
    workspace_artifacts: tuple[str, ...] = ()

    def prepare(self, session: SessionCtx) -> None:
        self._requested_model = session.model
        home = self._home(session)
        home.mkdir(parents=True, exist_ok=True)
        if not self._base_url(session):
            provider = session.requested_env.get("RP_PROVIDER", "provider").strip() or "provider"
            raise RuntimeError(
                f"provider {provider!r} does not declare an Anthropic Messages endpoint; "
                "add `protocols: [anthropic_messages]` and its root to config.yaml"
            )
        # Permission prompts and telemetry have no operator to answer them in a
        # batch run; the settings file states that once instead of per launch.
        (home / "settings.json").write_text(json.dumps({
            "includeCoAuthoredBy": False,
            "cleanupPeriodDays": 1,
        }, indent=2) + "\n", encoding="utf-8")
        servers = {
            name: spec
            for name, spec in ((session.mcp_config or {}).get("mcpServers", {}) or {}).items()
            if not spec.get("disabled")
        }
        if servers:
            self._mcp_file(session).write_text(
                json.dumps({"mcpServers": servers}, indent=2) + "\n", encoding="utf-8")

    def _base_url(self, session: SessionCtx) -> str:
        """Endpoint root for the Messages API, as Claude Code expects it."""
        env = session.requested_env
        declared = env.get("RP_PROVIDER_ANTHROPIC_BASE_URL", "").strip()
        if declared:
            return declared.rstrip("/")
        base = env.get("RP_PROVIDER_BASE_URL", "").strip().rstrip("/")
        return base[: -len("/v1")] if base.endswith("/v1") else base

    def _claude_argv(self, session: SessionCtx, resume: bool) -> list[str]:
        argv = [
            "claude", "--print",
            "--output-format", "stream-json", "--verbose",
            "--dangerously-skip-permissions",
            "--model", session.model,
            "--add-dir", str(session.workspace),
            "--settings", str(self._home(session) / "settings.json"),
        ]
        if resume:
            argv.append("--continue")
        mcp_file = self._mcp_file(session)
        if mcp_file.is_file():
            argv += ["--mcp-config", str(mcp_file)]
        return argv

    def _wrapped(self, session: SessionCtx, prompt_path: Path, resume: bool) -> CommandSpec:
        argv = [
            sys.executable, str(Path(__file__).parent / "run.py"),
            "--events", str(self._events_file(session)),
            "--prompt", str(prompt_path),
            "--model", session.model,
            "--", *self._claude_argv(session, resume),
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
        env["ANTHROPIC_BASE_URL"] = self._base_url(session)
        env["ANTHROPIC_AUTH_TOKEN"] = key
        # Cleared so the CLI cannot fall back to a real Anthropic subscription or
        # a stray key and quietly bill a different account than the run declares.
        env["ANTHROPIC_API_KEY"] = ""
        env["CLAUDE_CODE_OAUTH_TOKEN"] = ""
        env["CLAUDE_CONFIG_DIR"] = str(self._home(session))
        env["DISABLE_TELEMETRY"] = "1"
        env["DISABLE_AUTOUPDATER"] = "1"
        env["DISABLE_ERROR_REPORTING"] = "1"
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
