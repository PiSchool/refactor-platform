"""SSE: run status/task/metrics and per-session events.jsonl feed. Event-driven
via the hub; the session-events feed tails the file while the session runs.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select

from app.db import engine as db_engine
from app.db.models import AgentSession, Run
from app.catalog.bootstrap import bootstrap_error, data_state
from app.realtime.hub import hub

router = APIRouter(prefix="/api")


def _sse(event: str, data) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


# A comment line. EventSource ignores it, but it keeps the connection from
# looking idle to intermediaries that would otherwise time it out.
_HEARTBEAT = b": ping\n\n"
_HEARTBEAT_EVERY = 20.0

# `no-transform` forbids proxies from re-encoding the body. Without it the
# dashboard's Next.js proxy gzips the stream, and gzip buffers: nothing reaches
# the browser until the response closes — i.e. until the run ends. `curl` never
# saw this because it does not send Accept-Encoding.
# `X-Accel-Buffering: no` is the same instruction for nginx.
_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


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
    return StreamingResponse(gen(), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.get("/benchmarks/{key}/bootstrap/events")
async def benchmark_bootstrap_events(key: str, request: Request):
    """Push the terminal benchmark-data state once provisioning finishes.

    Provisioning streams recheck state immediately after arming their
    subscription, closing the race between the initial event and registration.
    """
    loaded = request.app.state.registry.benchmarks.get(key)
    if loaded is None:
        raise HTTPException(404, f"unknown benchmark: {key}")

    def payload(state: str) -> dict:
        return {
            "key": key,
            "dataState": state,
            "dataError": bootstrap_error(loaded),
        }

    initial_state = data_state(loaded)
    if initial_state != "provisioning":
        return Response(
            content=_sse("status", payload(initial_state)),
            media_type="text/event-stream",
            headers=_SSE_HEADERS,
        )

    async def gen():
        yield _sse("status", payload(initial_state))
        async with hub.listen(f"benchmark:{key}") as queue:
            # Arm the subscription, then re-read disk state. If completion
            # happened just before registration the recheck sees it; if it
            # happened just after, the queue receives the published event.
            state = data_state(loaded)
            if state != "provisioning":
                yield _sse("status", payload(state))
                return
            while True:
                event, data = await queue.get()
                yield _sse(event, data)
                if event == "status" and data.get("dataState") != "provisioning":
                    return

    return StreamingResponse(gen(), media_type="text/event-stream", headers=_SSE_HEADERS)


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
        async def load_session():
            async with db_engine.session_factory()() as s:
                return (await s.execute(
                    select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()

        async def read_new(path: Path | None, offset: int) -> tuple[list[bytes], int]:
            """Everything appended since `offset`, encoded as SSE frames."""
            if not (path and path.is_file()):
                return [], offset
            lines, offset = await asyncio.to_thread(_read_since, path, offset)
            frames = []
            for line in lines:
                if not line.strip():
                    continue
                try:
                    frames.append(_sse("event", json.loads(line)))
                except json.JSONDecodeError:
                    pass
            return frames, offset

        sess = await load_session()
        events_path = Path(sess.events_path) if sess and sess.events_path else None
        offset = 0
        last_beat = asyncio.get_event_loop().time()

        # The agent creates events.jsonl a while into the session, so the path may
        # not exist yet. Tail until the session ends; the client hanging up ends
        # this generator, so no arbitrary iteration cap is needed.
        while True:
            frames, offset = await read_new(events_path, offset)
            for frame in frames:
                yield frame

            sess = await load_session()
            if sess and sess.events_path and not events_path:
                events_path = Path(sess.events_path)
            if sess is None or sess.status != "running":
                break

            now = asyncio.get_event_loop().time()
            if not frames and now - last_beat >= _HEARTBEAT_EVERY:
                last_beat = now
                yield _HEARTBEAT
            await asyncio.sleep(0.5)

        # The agent writes session.shutdown as it exits, which can land between the
        # last read and the status flip. Drain once more so the final events — and
        # with them the exact prompt-token and context numbers — are never lost.
        frames, _ = await read_new(events_path, offset)
        for frame in frames:
            yield frame

        # Tell the client this stream is finished, not broken. Without it a client
        # that reconnects on failure would reconnect forever after every session.
        yield _sse("end", {"sessionId": session_id})

    return StreamingResponse(gen(), media_type="text/event-stream", headers=_SSE_HEADERS)
