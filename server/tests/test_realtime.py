from __future__ import annotations

import asyncio

import httpx
import pytest

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
async def test_terminal_log_after_run(client):
    run_id = await _launch(client)
    for _ in range(200):
        r = (await client.get(f"/api/runs/{run_id}")).json()
        if r["status"] == "completed":
            break
        await asyncio.sleep(0.1)
    tasks = (await client.get(f"/api/runs/{run_id}/tasks")).json()["tasks"]
    sess = tasks[0]["session"]
    log = await client.get(f"/api/sessions/{sess['id']}/terminal-log")
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
