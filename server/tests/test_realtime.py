from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest
from starlette.websockets import WebSocketState

from tests.helpers import FIXTURES


@pytest.fixture()
async def client(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    from app import config
    config.get_settings.cache_clear()
    from app.main import app
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def _launch(client):
    cat = (await client.get("/api/catalog")).json()
    bench = next(b for b in cat["benchmarks"] if b["key"] == "fixturebench")
    agent = next(a for a in cat["agents"] if a["key"] == "stub")
    body = {"benchmarkId": bench["id"], "setupId": "s1", "agentToolId": agent["id"],
            "model": "stub-model", "taskKeys": ["fixture-0001"], "taskTimeoutSeconds": 30}
    return (await client.post("/api/runs", json=body)).json()["id"]


@pytest.mark.asyncio
async def test_run_sse_emits_status(client):
    run_id = await _launch(client)
    events = []
    async with client.stream("GET", f"/api/runs/{run_id}/events") as resp:
        async for line in resp.aiter_lines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
            if line.startswith("data:") and '"completed"' in line:
                break
    assert "status" in events


@pytest.mark.asyncio
async def test_terminal_artifact_after_run(client):
    run_id = await _launch(client)
    for _ in range(200):
        r = (await client.get(f"/api/runs/{run_id}")).json()
        if r["status"] == "completed":
            break
        await asyncio.sleep(0.1)
    tasks = (await client.get(f"/api/runs/{run_id}/tasks")).json()["tasks"]
    sess = tasks[0]["session"]
    terminal = next(artifact for artifact in sess["artifacts"] if artifact["key"] == "terminal")
    assert terminal["available"] is True
    log = await client.get(terminal["viewUrl"])
    assert log.status_code == 200
    assert "[stub]" in log.text


@pytest.mark.asyncio
async def test_export_import_roundtrip(client):
    run_id = await _launch(client)
    for _ in range(200):
        if (await client.get(f"/api/runs/{run_id}")).json()["status"] == "completed":
            break
        await asyncio.sleep(0.1)
    zip_bytes = (await client.get(f"/api/runs/{run_id}/export")).content
    files = {"file": ("run.zip", zip_bytes, "application/zip")}
    imported = await client.post("/api/runs/import", files=files)
    assert imported.status_code == 201
    new_id = imported.json()["id"]
    detail = (await client.get(f"/api/runs/{new_id}")).json()
    assert detail["status"] == "completed"
    assert detail["counts"]["passed"] == 1


def test_sse_reads_only_appended_bytes(tmp_path):
    """The tailer re-read the whole events.jsonl every 0.5s. Once the file grew
    to megabytes that blocked the event loop and the UI saw 'socket hang up'."""
    from app.realtime.sse import _read_since

    p = tmp_path / "events.jsonl"
    p.write_text('{"a":1}\n{"a":2}\n')
    lines, off = _read_since(p, 0)
    assert lines == ['{"a":1}', '{"a":2}'] and off == p.stat().st_size

    # nothing new -> no work, offset unchanged
    assert _read_since(p, off) == ([], off)

    # append: only the new line comes back
    with p.open("a") as fh:
        fh.write('{"a":3}\n')
    lines2, off2 = _read_since(p, off)
    assert lines2 == ['{"a":3}'] and off2 == p.stat().st_size


def test_sse_holds_back_partial_trailing_line(tmp_path):
    """A half-written JSON line must not be emitted (or skipped) — it is kept
    until its newline arrives."""
    from app.realtime.sse import _read_since

    p = tmp_path / "events.jsonl"
    p.write_text('{"a":1}\n{"partial"')
    lines, off = _read_since(p, 0)
    assert lines == ['{"a":1}']

    with p.open("a") as fh:
        fh.write(':2}\n')
    lines2, _ = _read_since(p, off)
    assert lines2 == ['{"partial":2}']


def test_sse_forbids_proxy_recompression():
    """Next.js gzips proxied responses by default, and gzip buffers a stream:
    without `no-transform` the browser sees nothing until the run ends."""
    from app.realtime.sse import _SSE_HEADERS

    assert "no-transform" in _SSE_HEADERS["Cache-Control"]
    assert _SSE_HEADERS["X-Accel-Buffering"] == "no"


@pytest.mark.asyncio
async def test_pty_append_preserves_first_process_transcript(tmp_path):
    import sys

    from app.catalog.sdk import CommandSpec
    from app.execution.pty_host import run_pty

    terminal = tmp_path / "terminal.log"
    first = CommandSpec([sys.executable, "-c", "print('first')"], {}, tmp_path)
    second = CommandSpec([sys.executable, "-c", "print('second')"], {}, tmp_path)

    await run_pty(first, terminal, lambda _chunk: None, 5)
    await run_pty(second, terminal, lambda _chunk: None, 5, append=True)

    text = terminal.read_text(encoding="utf-8")
    assert "first" in text
    assert "second" in text
    assert text.index("first") < text.index("second")


class _RecordingSocket:
    def __init__(self, on_status=None, on_bytes=None):
        self.client_state = WebSocketState.CONNECTED
        self.statuses = []
        self.chunks = []
        self._on_status = on_status
        self._on_bytes = on_bytes

    async def send_json(self, payload):
        self.statuses.append(payload)
        if self._on_status:
            await self._on_status(payload)

    async def send_bytes(self, payload):
        self.chunks.append(payload)
        if self._on_bytes:
            await self._on_bytes(payload)


@pytest.mark.asyncio
async def test_terminal_completed_replay_honors_resume_offset(tmp_path):
    from app.realtime.ws_terminal import _stream_terminal

    terminal = tmp_path / "terminal.log"
    terminal.write_bytes(b"alpha-beta")
    socket = _RecordingSocket()

    await _stream_terminal(
        socket,
        "session",
        terminal,
        live=False,
        resume_offset=6,
        is_live=lambda: asyncio.sleep(0, result=False),
        poll_interval=0.01,
    )

    assert b"".join(socket.chunks) == b"beta"
    assert socket.statuses[-1] == {"type": "status", "state": "ended", "offset": 10}


@pytest.mark.asyncio
async def test_terminal_replay_to_live_handoff_has_no_duplicate_or_lost_bytes(tmp_path):
    from app.realtime.hub import TerminalChunk, hub
    from app.realtime.ws_terminal import _stream_terminal

    hub.bind_loop(asyncio.get_running_loop())
    terminal = tmp_path / "terminal.log"
    terminal.write_bytes(b"before-")
    published = False

    async def publish_during_handoff(payload):
        nonlocal published
        if payload.get("state") != "live" or published:
            return
        published = True
        with terminal.open("ab") as handle:
            handle.write(b"during-")
            handle.flush()
        hub.publish(
            "terminal:session",
            "bytes",
            TerminalChunk(offset=7, data=b"during-"),
        )

    socket = _RecordingSocket(on_status=publish_during_handoff)
    await _stream_terminal(
        socket,
        "session",
        terminal,
        live=True,
        resume_offset=0,
        is_live=lambda: asyncio.sleep(0, result=False),
        poll_interval=0.01,
    )

    assert b"".join(socket.chunks) == b"before-during-"
    assert socket.statuses[0]["state"] == "live"
    assert socket.statuses[-1] == {"type": "status", "state": "ended", "offset": 14}


@pytest.mark.asyncio
async def test_terminal_live_delta_continues_from_replayed_offset(tmp_path):
    from app.realtime.hub import TerminalChunk, hub
    from app.realtime.ws_terminal import _stream_terminal

    hub.bind_loop(asyncio.get_running_loop())
    terminal = tmp_path / "terminal.log"
    terminal.write_bytes(b"old-")
    published = False

    async def publish_after_replay(_payload):
        nonlocal published
        if published:
            return
        published = True
        with terminal.open("ab") as handle:
            handle.write(b"new")
            handle.flush()
        hub.publish(
            "terminal:session",
            "bytes",
            TerminalChunk(offset=4, data=b"new"),
        )

    socket = _RecordingSocket(on_bytes=publish_after_replay)
    live_checks = 0

    async def is_live():
        nonlocal live_checks
        live_checks += 1
        return live_checks == 1

    await _stream_terminal(
        socket,
        "session",
        terminal,
        live=True,
        resume_offset=0,
        is_live=is_live,
        poll_interval=0.01,
    )

    assert b"".join(socket.chunks) == b"old-new"


@pytest.mark.asyncio
async def test_session_events_replays_then_ends_cleanly(tmp_env, tmp_path):
    """Replay the whole file, never drop the final event, and finish with `end`
    so a reconnecting client knows the session is over rather than broken."""
    from app.db import engine as db_engine
    from app.db.models import AgentSession, AgentTool, Benchmark, Run, RunTask, Task
    from app.realtime.sse import session_events

    await db_engine.migrate()
    events = tmp_path / "events.jsonl"
    events.write_text('{"type":"session.start"}\n{"type":"session.shutdown"}\n')

    async with db_engine.session_factory()() as s:
        bench = Benchmark(key="b", name="B", language="python", manifest={})
        tool = AgentTool(key="t", name="T", manifest={})
        s.add_all([bench, tool]); await s.flush()
        task = Task(benchmark_id=bench.id, task_key="k", title="T", language="python",
                    workspace={"type": "snapshot", "source": "r"}, instructions="i", params={})
        s.add(task); await s.flush()
        run = Run(benchmark_id=bench.id, agent_tool_id=tool.id, setup_key="s1",
                  model="m", task_timeout_seconds=60)
        s.add(run); await s.flush()
        rt = RunTask(run_id=run.id, task_id=task.id, ordinal=0, timeout_seconds=60)
        s.add(rt); await s.flush()
        sess = AgentSession(run_task_id=rt.id, status="ended", events_path=str(events))
        s.add(sess); await s.commit()
        sid = sess.id

    resp = await session_events(sid)
    assert "no-transform" in resp.headers["cache-control"]
    assert resp.headers["x-accel-buffering"] == "no"

    body = b"".join([chunk async for chunk in resp.body_iterator]).decode()
    assert body.count("event: event") == 2       # both lines replayed
    assert "session.shutdown" in body            # the final event is never dropped
    assert "event: end" in body                  # "finished", not "broken"
