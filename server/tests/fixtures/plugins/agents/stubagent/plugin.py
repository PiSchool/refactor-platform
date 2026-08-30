"""Stub agent adapter. Imports ONLY from app.catalog.sdk (boundary check)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

CLI = str(Path(__file__).parent / "stub_cli.py")


class Plugin(AgentPlugin):
    capabilities = {"lsp": True, "subagents": True, "eval_tool": True, "retrieval": True}

    def prepare(self, session: SessionCtx) -> None:
        session.config_dir.mkdir(parents=True, exist_ok=True)

    def command(self, session: SessionCtx) -> CommandSpec:
        argv = [sys.executable, CLI, str(session.workspace), str(self.events_path(session))]
        argv += ["--setup", session.setup.key]
        # A task can ask for a slow session, which is how a test observes a run
        # while it is still running.
        sleep = session.task.params.get("sleepSeconds")
        if sleep:
            argv += ["--sleep", str(sleep)]
        argv += session.extra.get("stub_args", [])
        return CommandSpec(argv=argv, env=dict(session.requested_env), cwd=session.workspace)

    def resume_command(self, session: SessionCtx, prompt_path: Path) -> CommandSpec:
        argv = [sys.executable, CLI, str(session.workspace), str(self.events_path(session))]
        argv += ["--setup", session.setup.key, "--noedit", "--append-events"]
        return CommandSpec(argv=argv, env=dict(session.requested_env), cwd=session.workspace)

    def events_path(self, session: SessionCtx) -> Path:
        return session.config_dir / "events.jsonl"

    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo:
        info = SessionInfo(model="stub-model")
        if events_path and events_path.is_file():
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                ev = json.loads(line)
                if ev.get("type") == "assistant.message":
                    info.response_text = ev["data"].get("content", "")
                if ev.get("type") == "session.shutdown":
                    mm = ev["data"].get("modelMetrics", {})
                    for m, v in mm.items():
                        info.model = m
                        u = v.get("usage", {})
                        info.tokens_input += int(u.get("inputTokens", 0))
                        info.tokens_output += int(u.get("outputTokens", 0))
                if ev.get("type") == "tool.execution_start":
                    tool = ev.get("data", {}).get("toolName", "")
                    arguments = str(ev.get("data", {}).get("arguments", ""))
                    if tool == "lsp":
                        info.lsp_actions += 1
                    elif tool == "task":
                        info.subagent_invocations += 1
                    if "eval.sh" in arguments:
                        info.eval_iterations += 1
                        info.eval_tool_invocations += 1
        info.readable_transcript = info.response_text
        return info
