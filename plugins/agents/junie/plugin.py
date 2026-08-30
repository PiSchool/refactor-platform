"""Junie CLI adapter (JetBrains).

Junie reaches a model either through a JetBrains subscription or through its own
key. The platform uses neither: it writes a custom model profile naming the
endpoint it resolved, so the request goes to the provider the run declares and
nothing is billed to a JetBrains account. The profile references the key by
environment variable, which Junie expands, so no secret is written to disk.

Junie is given `--task`, which runs the task and exits. Its other entry point,
`--prompt`, opens the interactive terminal interface with the text already
submitted; with no terminal to answer, that ended the session in seconds without
touching the repository. Brave mode is enabled in the session's own
configuration because a benchmark run has no operator to approve an action.

Everything Junie keeps — settings, sessions, logs, credentials, MCP servers and
model profiles — lives under `JUNIE_HOME`, pointed at the session's private
directory, so two tasks cannot read each other's state.

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

#: Filename of the custom model profile, which is also its id: Junie selects it
#: as `custom:<profile-id>`.
PROFILE = "platform"


class Plugin(AgentPlugin):
    capabilities = {"lsp": False, "subagents": True, "eval_tool": True, "retrieval": True}
    models: list[str] = []
    _requested_model = ""

    # Junie keeps its state under JUNIE_HOME, outside the workspace, so nothing
    # of its own lands in the captured diff.
    workspace_artifacts: tuple[str, ...] = ()

    def _home(self, session: SessionCtx) -> Path:
        return session.config_dir / ".junie"

    def _events_file(self, session: SessionCtx) -> Path:
        return session.config_dir / "events.jsonl"

    def prepare(self, session: SessionCtx) -> None:
        self._requested_model = session.model
        env = session.requested_env
        base_url = env.get("RP_PROVIDER_BASE_URL", "").strip().rstrip("/")
        provider = env.get("RP_PROVIDER", "provider").strip() or "provider"
        if not base_url:
            raise RuntimeError(
                f"no base URL configured for provider {provider!r}; "
                "set it in config.yaml or its base-URL environment variable"
            )
        if not env.get("RP_PROVIDER_API_KEY", "").strip():
            raise RuntimeError(
                f"no API key configured for provider {provider!r}; "
                "set its API-key environment variable in .env"
            )
        home = self._home(session)
        (home / "models").mkdir(parents=True, exist_ok=True)
        # A profile's baseUrl is the complete endpoint, not a prefix Junie
        # extends, so the chat-completions path is spelled out here.
        (home / "models" / f"{PROFILE}.json").write_text(json.dumps({
            "baseUrl": f"{base_url}/chat/completions",
            "id": session.model,
            "apiType": "OpenAICompletion",
            "apiKey": "${RP_PROVIDER_API_KEY}",
        }, indent=2) + "\n", encoding="utf-8")
        (home / "config.json").write_text(json.dumps({
            "model": f"custom:{PROFILE}",
            "brave": True,                 # no operator is present to approve a tool
            "auto-update": False,
            "model-default-locations": True,
        }, indent=2) + "\n", encoding="utf-8")
        servers = {
            name: spec
            for name, spec in ((session.mcp_config or {}).get("mcpServers", {}) or {}).items()
            if not spec.get("disabled")
        }
        if servers:
            (home / "mcp").mkdir(parents=True, exist_ok=True)
            (home / "mcp" / "mcp.json").write_text(
                json.dumps({"mcpServers": servers}, indent=2) + "\n", encoding="utf-8")

    def _session_file(self, session: SessionCtx) -> Path:
        """Where the wrapper records the session id Junie assigned."""
        return session.config_dir / "junie-session-id"

    def _junie_argv(self, session: SessionCtx, resume: bool) -> list[str]:
        argv = [
            "junie",
            "--model", f"custom:{PROFILE}",
            "--skip-update-check",
            "--output-format", "json-stream",
        ]
        recorded = self._session_file(session)
        if resume and recorded.is_file():
            session_id = recorded.read_text(encoding="utf-8").strip()
            if session_id:
                argv += ["--session-id", session_id]
        return argv

    def _wrapped(self, session: SessionCtx, prompt_path: Path, resume: bool) -> CommandSpec:
        argv = [
            sys.executable, str(Path(__file__).parent / "run.py"),
            "--events", str(self._events_file(session)),
            "--prompt", str(prompt_path),
            "--model", session.model,
            "--junie-home", str(self._home(session)),
            "--session-file", str(self._session_file(session)),
            "--", *self._junie_argv(session, resume),
        ]
        return CommandSpec(argv=argv, env=self._env(session), cwd=session.workspace)

    def command(self, session: SessionCtx) -> CommandSpec:
        return self._wrapped(session, session.prompt_path, resume=False)

    def resume_command(self, session: SessionCtx, prompt_path: Path) -> CommandSpec:
        return self._wrapped(session, prompt_path, resume=True)

    def _env(self, session: SessionCtx) -> dict[str, str]:
        env = dict(session.requested_env)
        env["JUNIE_HOME"] = str(self._home(session))
        # Cleared so Junie cannot fall back to a JetBrains subscription or an
        # internal gateway and bill an account the run does not declare.
        env["JUNIE_API_KEY"] = ""
        env["EJ_AUTH_INGRAZZIO_TOKEN"] = ""
        env["INGRAZZIO_URL"] = ""
        env["JUNIE_SHARE_ANONYMOUS_STATISTICS"] = "false"
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
