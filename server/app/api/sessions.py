"""Session artifacts.

These read files that reach tens of megabytes (terminal.log, diffs). The reads
are pushed off the event loop — doing them inline stalled every other request,
which surfaced in the browser as `socket hang up`.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select

from app.config import get_settings
from app.db import engine as db_engine
from app.db.models import AgentSession

router = APIRouter(prefix="/api")

_TEXT = "text/plain; charset=utf-8"


def _read(path: Path | None) -> str:
    if not path or not path.is_file():
        return ""
    return path.read_bytes().decode("utf-8", errors="replace")


@router.get("/artifact")
def artifact(path: str):
    """Serve a persisted artifact by path, guarded to the outputs directory.
    Declared `def` so FastAPI runs it in its threadpool."""
    outputs = get_settings().outputs_dir.resolve()
    p = Path(path).resolve()
    if outputs not in p.parents:
        raise HTTPException(403, "path outside outputs")
    if not p.is_file():
        raise HTTPException(404, "not found")
    return PlainTextResponse(p.read_text(encoding="utf-8", errors="replace"), media_type=_TEXT)


async def _session(session_id: str) -> AgentSession:
    async with db_engine.session_factory()() as s:
        sess = (await s.execute(select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
        if sess is None:
            raise HTTPException(404, "unknown session")
        return sess


@router.get("/sessions/{session_id}/terminal-log")
async def terminal_log(session_id: str):
    sess = await _session(session_id)
    path = Path(sess.terminal_path) if sess.terminal_path else None
    return PlainTextResponse(await asyncio.to_thread(_read, path), media_type=_TEXT)


@router.get("/sessions/{session_id}/transcript")
async def transcript(session_id: str):
    sess = await _session(session_id)
    path = Path(sess.terminal_path).parent / "transcript.txt" if sess.terminal_path else None
    return PlainTextResponse(await asyncio.to_thread(_read, path), media_type=_TEXT)
