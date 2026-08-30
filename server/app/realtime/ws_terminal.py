"""Lossless read-only terminal replay and live byte streaming."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Awaitable, Callable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from starlette.websockets import WebSocketState

from app.db import engine as db_engine
from app.db.models import AgentSession
from app.config import REPO_ROOT, get_settings
from app.realtime.hub import TerminalChunk, hub
from app.results.redaction import Redactor

router = APIRouter()


async def _close(ws: WebSocket) -> None:
    """Closing a socket the client already dropped raises RuntimeError
    ('Cannot call "send" once a close message has been sent')."""
    if ws.client_state is WebSocketState.CONNECTED:
        try:
            await ws.close()
        except RuntimeError:
            pass


def _read_range(path: Path | None, start: int, end: int | None = None) -> bytes:
    if path is None or not path.is_file():
        return b""
    with path.open("rb") as handle:
        handle.seek(start)
        return handle.read() if end is None else handle.read(max(0, end - start))


def _redacted_reader(private_root: Path):
    settings = get_settings()
    redactor = Redactor.from_environment(private_paths=(
        private_root,
        settings.outputs_dir,
        settings.data_dir,
        REPO_ROOT,
    ))

    def read(path: Path | None, start: int, end: int | None = None) -> bytes:
        if path is None or not path.is_file():
            return b""
        content = b"".join(
            redactor.iter_text(path, chunk_size=settings.evidence.stream_chunk_bytes)
        )
        return content[start:] if end is None else content[start:end]

    return read


async def _send_file_range(
    ws: WebSocket,
    path: Path | None,
    start: int,
    end: int | None = None,
    reader: Callable[[Path | None, int, int | None], bytes] = _read_range,
) -> int:
    data = await asyncio.to_thread(reader, path, start, end)
    if data:
        await ws.send_bytes(data)
    return start + len(data)


async def _send_chunk(
    ws: WebSocket,
    path: Path | None,
    sent: int,
    chunk: TerminalChunk,
    reader: Callable[[Path | None, int, int | None], bytes] = _read_range,
) -> int:
    end = chunk.offset + len(chunk.data)
    if end <= sent:
        return sent
    if chunk.offset > sent:
        for _ in range(20):
            sent = await _send_file_range(
                ws, path, sent, chunk.offset, reader=reader
            )
            if sent >= chunk.offset:
                break
            await asyncio.sleep(0.01)
        if sent < chunk.offset:
            raise RuntimeError("terminal log has an unrecoverable byte gap")
    delta = chunk.data[max(0, sent - chunk.offset):]
    if delta:
        await ws.send_bytes(delta)
        sent += len(delta)
    return sent


async def _stream_terminal(
    ws: WebSocket,
    session_id: str,
    log_path: Path | None,
    *,
    live: bool,
    resume_offset: int,
    is_live: Callable[[], Awaitable[bool]],
    poll_interval: float = 1.0,
    reader: Callable[[Path | None, int, int | None], bytes] = _read_range,
) -> None:
    """Subscribe before replay, then deduplicate overlap using byte offsets."""
    topic = f"terminal:{session_id}"
    async with hub.listen(topic) as queue:
        if reader is _read_range:
            size = log_path.stat().st_size if log_path and log_path.is_file() else 0
        else:
            size = len(await asyncio.to_thread(reader, log_path, 0, None))
        reset = resume_offset > size
        sent = 0 if reset else resume_offset
        if live:
            status = {"type": "status", "state": "live", "offset": sent}
            if reset:
                status["reset"] = True
            await ws.send_json(status)

        sent = await _send_file_range(ws, log_path, sent, reader=reader)
        if not live:
            await ws.send_json({"type": "status", "state": "ended", "offset": sent})
            return

        while True:
            try:
                _event, chunk = await asyncio.wait_for(queue.get(), timeout=poll_interval)
                if isinstance(chunk, TerminalChunk):
                    sent = await _send_chunk(
                        ws, log_path, sent, chunk, reader=reader
                    )
            except asyncio.TimeoutError:
                if await is_live():
                    continue
                while not queue.empty():
                    _event, chunk = queue.get_nowait()
                    if isinstance(chunk, TerminalChunk):
                        sent = await _send_chunk(
                            ws, log_path, sent, chunk, reader=reader
                        )
                sent = await _send_file_range(
                    ws, log_path, sent, reader=reader
                )
                await ws.send_json(
                    {"type": "status", "state": "ended", "offset": sent}
                )
                return


@router.websocket("/ws/sessions/{session_id}/terminal")
async def terminal(ws: WebSocket, session_id: str):
    try:
        resume_offset = int(ws.query_params.get("offset", "0"))
        if resume_offset < 0:
            raise ValueError
    except ValueError:
        await ws.close(code=1008, reason="invalid terminal offset")
        return

    await ws.accept()
    async with db_engine.session_factory()() as s:
        sess = (await s.execute(select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
    if sess is None:
        await ws.send_json({"type": "status", "state": "ended", "offset": 0})
        await _close(ws)
        return

    raw_log_path = Path(sess.terminal_path) if sess.terminal_path else None
    live = sess.status == "running"
    if live and raw_log_path is not None:
        log_path = raw_log_path.parent / ".terminal.redacted"
        reader = _read_range
    else:
        log_path = raw_log_path
        reader = (
            _redacted_reader(raw_log_path.parent)
            if raw_log_path is not None
            else _read_range
        )

    async def session_is_live() -> bool:
        async with db_engine.session_factory()() as s:
            fresh = (
                await s.execute(
                    select(AgentSession).where(AgentSession.id == session_id)
                )
            ).scalar_one_or_none()
        return fresh is not None and fresh.status == "running"

    try:
        await _stream_terminal(
            ws,
            session_id,
            log_path,
            live=live,
            resume_offset=resume_offset,
            is_live=session_is_live,
            reader=reader,
        )
    except WebSocketDisconnect:
        pass
    finally:
        await _close(ws)
