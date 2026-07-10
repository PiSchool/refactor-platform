"""Read-only terminal bridge: send terminal.log from byte 0 (full scrollback),
then stream live bytes from the hub. On end, the client loads the finalized
log via the REST endpoint.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from starlette.websockets import WebSocketState

from app.db import engine as db_engine
from app.db.models import AgentSession
from app.realtime.hub import hub

router = APIRouter()


async def _close(ws: WebSocket) -> None:
    """Closing a socket the client already dropped raises RuntimeError
    ('Cannot call "send" once a close message has been sent')."""
    if ws.client_state is WebSocketState.CONNECTED:
        try:
            await ws.close()
        except RuntimeError:
            pass


@router.websocket("/ws/sessions/{session_id}/terminal")
async def terminal(ws: WebSocket, session_id: str):
    await ws.accept()
    async with db_engine.session_factory()() as s:
        sess = (await s.execute(select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
    if sess is None:
        await ws.send_json({"type": "status", "state": "ended"})
        await _close(ws)
        return

    log_path = Path(sess.terminal_path) if sess.terminal_path else None
    live = sess.status == "running"
    await ws.send_json({"type": "status", "state": "live" if live else "ended"})

    # replay whatever exists on disk now
    sent = 0
    if log_path and log_path.is_file():
        data = log_path.read_bytes()
        await ws.send_bytes(data)
        sent = len(data)

    if not live:
        await _close(ws)
        return

    queue: asyncio.Queue = asyncio.Queue()

    async def pump():
        async for _event, chunk in hub.subscribe(f"terminal:{session_id}"):
            await queue.put(chunk)

    pump_task = asyncio.create_task(pump())
    try:
        while True:
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
                await ws.send_bytes(chunk)
            except asyncio.TimeoutError:
                async with db_engine.session_factory()() as s:
                    fresh = (await s.execute(
                        select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
                if fresh is None or fresh.status != "running":
                    await ws.send_json({"type": "status", "state": "ended"})
                    break
    except WebSocketDisconnect:
        pass
    finally:
        pump_task.cancel()
        await _close(ws)
