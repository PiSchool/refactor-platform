"""GitHub Copilot CLI agent adapter (BYOK via OpenRouter, verified on 1.0.68).

The platform owns the PTY lifecycle; this adapter only prepares the private
config dir, builds the launch command, locates the event log, and parses the
session. Imports ONLY from app.catalog.sdk.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import events as events_mod  # noqa: E402

from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo  # noqa: E402


class Plugin(AgentPlugin):
    capabilities = {"lsp": True, "subagents": True, "eval_tool": True}
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

    def command(self, session: SessionCtx) -> CommandSpec:
        argv = [
            "copilot", "--allow-all", "--no-custom-instructions", "--no-ask-user",
            "--no-auto-update", "--max-autopilot-continues", "200",
            "--model", session.model,
        ]
        if not session.setup.subagents:
            argv += ["--excluded-tools", "task"]
        argv += ["--add-dir", str(session.workspace), "--autopilot",
                 "--name", session.session_id, "-p", f"@{session.prompt_path}"]
        return CommandSpec(argv=argv, env=self._env(session), cwd=session.workspace)

    def _env(self, session: SessionCtx) -> dict[str, str]:
        env = dict(session.requested_env)
        env["COPILOT_CONFIG_DIR"] = str(self._copilot_home(session))
        key = env.get("OPENROUTER_API_KEY", "").strip()
        if key:  # BYOK: route Copilot at OpenRouter, disable GitHub auth path
            env["COPILOT_PROVIDER_BASE_URL"] = env.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
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
