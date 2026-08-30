"""The smallest adapter that produces a readable run.

An adapter answers four questions: what to run, where its machine-readable
event log will be, how to read that log back, and what to clean up. The
platform owns the process, the terminal, the timeout and the diff.

`session.py` is imported relatively, so a second plugin shipping a module of
the same name cannot answer for this one.

Imports only from `app.catalog.sdk`, which is the whole plugin contract.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

from . import session as transcript

SCRIPT = Path(__file__).parent / "agent.sh"


class Plugin(AgentPlugin):
    #: The request format this CLI sends. A provider that does not answer it is
    #: refused before the run starts. This one calls no model at all.
    wire = "chat_completions"

    def prepare(self, session: SessionCtx) -> None:
        """Write whatever the CLI reads before it starts."""
        session.config_dir.mkdir(parents=True, exist_ok=True)

    def command(self, session: SessionCtx) -> CommandSpec:
        return CommandSpec(
            argv=["bash", str(SCRIPT), str(session.prompt_path), str(self.events_path(session))],
            env=dict(session.requested_env),
            cwd=session.workspace,
        )

    def events_path(self, session: SessionCtx) -> Path:
        return session.config_dir / "events.jsonl"

    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo:
        """Read the session back. Called for every task, including a failed one,
        so it must not raise when the log is empty or absent."""
        return transcript.read(events_path)

    def cleanup(self, session: SessionCtx) -> None:
        return None
