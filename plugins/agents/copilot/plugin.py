"""GitHub Copilot CLI agent adapter (BYOK, verified on 1.0.68).

The CLI is pointed at whichever OpenAI-compatible provider the platform has
selected, so the usable models are the operator's, not a list fixed here.

The platform owns the PTY lifecycle; this adapter only prepares the private
config dir, builds the launch command, locates the event log, and parses the
session. Imports ONLY from app.catalog.sdk.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

# A plugin's own modules are imported relative to it. Bare `import events`
# would collide with the other adapters, which ship a module of that name too.
from . import events as events_mod


class Plugin(AgentPlugin):
    capabilities = {"lsp": True, "subagents": True, "eval_tool": True, "retrieval": True}
    models = ["openrouter/free"]
    # written by prepare() into the workspace; never part of the agent's diff
    workspace_artifacts = (".github/lsp.json",)
    _requested_model = ""

    def _copilot_home(self, session: SessionCtx) -> Path:
        return session.config_dir / ".copilot"

    def prepare(self, session: SessionCtx) -> None:
        self._requested_model = session.model
        home = self._copilot_home(session)
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.json").write_text(
            json.dumps({"trustedFolders": [str(session.workspace)]}), encoding="utf-8")
        if session.lsp_config:
            (home / "lsp-config.json").write_text(
                json.dumps(session.lsp_config, indent=2), encoding="utf-8")
            gh = session.workspace / ".github"
            gh.mkdir(parents=True, exist_ok=True)
            (gh / "lsp.json").write_text(json.dumps(session.lsp_config, indent=2), encoding="utf-8")
        if session.mcp_config:
            (home / "mcp-config.json").write_text(
                json.dumps(session.mcp_config, indent=2), encoding="utf-8"
            )

    def _base_argv(self, session: SessionCtx) -> list[str]:
        argv = [
            "copilot", "--allow-all", "--no-custom-instructions", "--no-ask-user",
            "--no-auto-update", "--max-autopilot-continues", "200",
            "--model", session.model,
        ]
        if not session.setup.subagents:
            argv += ["--excluded-tools", "task"]
        if session.mcp_config:
            argv += ["--additional-mcp-config", f"@{self._copilot_home(session) / 'mcp-config.json'}"]
        argv += ["--add-dir", str(session.workspace), "--autopilot"]
        return argv

    def command(self, session: SessionCtx) -> CommandSpec:
        argv = self._base_argv(session)
        argv += ["--name", session.session_id, "-p", f"@{session.prompt_path}"]
        return CommandSpec(argv=argv, env=self._env(session), cwd=session.workspace)

    def resume_command(self, session: SessionCtx, prompt_path: Path) -> CommandSpec:
        argv = self._base_argv(session)
        argv += [f"--resume={session.session_id}", "-p", f"@{prompt_path}"]
        return CommandSpec(argv=argv, env=self._env(session), cwd=session.workspace)

    def _env(self, session: SessionCtx) -> dict[str, str]:
        env = dict(session.requested_env)
        env["COPILOT_CONFIG_DIR"] = str(self._copilot_home(session))
        provider = env.get("RP_PROVIDER", "provider").strip() or "provider"
        key = env.get("RP_PROVIDER_API_KEY", "").strip()
        base_url = env.get("RP_PROVIDER_BASE_URL", "").strip()
        if not base_url:
            raise RuntimeError(
                f"no base URL configured for provider {provider!r}; "
                "set it in config.yaml or its base-URL environment variable"
            )
        if not key:
            raise RuntimeError(
                f"no API key configured for provider {provider!r}; "
                "set its API-key environment variable in .env"
            )
        env["COPILOT_PROVIDER_BASE_URL"] = base_url
        env["COPILOT_PROVIDER_API_KEY"] = key
        env["COPILOT_PROVIDER_TYPE"] = "openai"
        env["COPILOT_MODEL"] = session.model
        env["COPILOT_GITHUB_TOKEN"] = ""
        return env

    def events_path(self, session: SessionCtx) -> Path | None:
        state = self._copilot_home(session) / "session-state"
        if not state.is_dir():
            return None
        # events land in a uuid dir (not --name); pick the newest with events.jsonl
        candidates = [d / "events.jsonl" for d in state.iterdir() if (d / "events.jsonl").is_file()]
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.stat().st_mtime)

    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo:
        return events_mod.parse(events_path, terminal_log_path, self._requested_model)

    def cleanup(self, session: SessionCtx) -> None:
        return None
