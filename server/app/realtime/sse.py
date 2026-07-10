"""SSE: run status/task/metrics and per-session events.jsonl feed. Event-driven
via the hub; the session-events feed tails the file while the session runs.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.db import engine as db_engine
from app.db.models import AgentSession, Run
from app.realtime.hub import hub

router = APIRouter(prefix="/api")


def _sse(event: str, data) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


@router.get("/runs/{run_id}/events")
async def run_events(run_id: str):
    async def gen():
        async with db_engine.session_factory()() as s:
            run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
            if run is not None:
                yield _sse("status", {"runStatus": run.status})
        async for event, data in hub.subscribe(f"run:{run_id}"):
            yield _sse(event, data)
            if event == "status" and data.get("runStatus") in ("completed", "stopped", "failed"):
                break
    return StreamingResponse(gen(), media_type="text/event-stream")


def _read_since(path: Path, offset: int) -> tuple[list[str], int]:
    """Read only what was appended. Re-reading the whole file each tick blocked
    the event loop for seconds once events.jsonl grew to megabytes."""
    with path.open("rb") as fh:
        fh.seek(offset)
        chunk = fh.read()
    if not chunk:
        return [], offset
    text = chunk.decode("utf-8", errors="ignore")
    # keep a trailing partial line for the next read
    complete, _, remainder = text.rpartition("\n")
    if not complete:
        return [], offset
    return complete.splitlines(), offset + len(chunk) - len(remainder.encode("utf-8"))


@router.get("/sessions/{session_id}/events")
async def session_events(session_id: str):
    async def gen():
        async with db_engine.session_factory()() as s:
            sess = (await s.execute(select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
        events_path = Path(sess.events_path) if sess and sess.events_path else None
        offset = 0
        for _ in range(3600):  # ~ up to 30 min of tailing at 0.5s
            if events_path and events_path.is_file():
                lines, offset = await asyncio.to_thread(_read_since, events_path, offset)
                for line in lines:
                    if line.strip():
                        try:
                            yield _sse("event", json.loads(line))
                        except json.JSONDecodeError:
                            pass
            async with db_engine.session_factory()() as s:
                sess = (await s.execute(select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
                if sess and sess.events_path and not events_path:
                    events_path = Path(sess.events_path)
                if sess and sess.status != "running":
                    break
            await asyncio.sleep(0.5)
    return StreamingResponse(gen(), media_type="text/event-stream")
