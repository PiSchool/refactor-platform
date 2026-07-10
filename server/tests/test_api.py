from __future__ import annotations

import asyncio

import httpx
import pytest

from tests.helpers import FIXTURES


async def _wait_run(client, run_id, status, timeout=20):
    for _ in range(int(timeout * 10)):
        r = await client.get(f"/api/runs/{run_id}")
        if r.json()["status"] == status:
            return r.json()
        await asyncio.sleep(0.1)
    return None


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


@pytest.mark.asyncio
async def test_health_and_catalog(client):
    assert (await client.get("/api/health")).json()["status"] == "ok"
    cat = (await client.get("/api/catalog")).json()
    assert any(b["key"] == "fixturebench" for b in cat["benchmarks"])
    assert any(a["key"] == "stub" for a in cat["agents"])
    assert {s["key"] for s in cat["setups"]} == {"s1", "s1_lsp", "s1_eval", "s3"}


@pytest.mark.asyncio
async def test_full_run_lifecycle(client):
    cat = (await client.get("/api/catalog")).json()
    bench = next(b for b in cat["benchmarks"] if b["key"] == "fixturebench")
    agent = next(a for a in cat["agents"] if a["key"] == "stub")
    body = {"benchmarkId": bench["id"], "setupId": "s1", "agentToolId": agent["id"],
            "model": "stub-model", "taskKeys": ["fixture-0001"], "taskTimeoutSeconds": 30}
    created = (await client.post("/api/runs", json=body)).json()
    run_id = created["id"]
    done = await _wait_run(client, run_id, "completed")
    assert done is not None
    assert done["counts"]["passed"] == 1
    assert done["passRate"] == 1.0

    # export
    exp = await client.get(f"/api/runs/{run_id}/export")
    assert exp.status_code == 200
    assert exp.headers["content-type"] == "application/zip"

    # restart clones
    r2 = (await client.post(f"/api/runs/{run_id}/restart")).json()
    assert r2["id"] != run_id
    await _wait_run(client, r2["id"], "completed")

    # delete original
    d = await client.delete(f"/api/runs/{run_id}")
    assert d.status_code == 200
    assert (await client.get(f"/api/runs/{run_id}")).status_code == 404


@pytest.mark.asyncio
async def test_create_validation(client):
    cat = (await client.get("/api/catalog")).json()
    bench = next(b for b in cat["benchmarks"] if b["key"] == "fixturebench")
    agent = next(a for a in cat["agents"] if a["key"] == "stub")
    # unsupported setup for this benchmark (fixturebench supports s1, s1_eval only)
    body = {"benchmarkId": bench["id"], "setupId": "s3", "agentToolId": agent["id"],
            "model": "m", "taskKeys": ["fixture-0001"], "taskTimeoutSeconds": 30}
    assert (await client.post("/api/runs", json=body)).status_code == 422
    # unknown task
    body["setupId"] = "s1"
    body["taskKeys"] = ["nope"]
    assert (await client.post("/api/runs", json=body)).status_code == 422


@pytest.mark.asyncio
async def test_settings_roundtrip(client):
    doc = (await client.get("/api/settings")).json()
    assert "editable" in doc and "secrets" in doc
    upd = (await client.put("/api/settings", json={"retentionCap": 5})).json()
    assert upd["editable"]["retentionCap"] == 5
    bad = await client.put("/api/settings", json={"activeModel": "x", "bogus": 1})
    # bogus is ignored by schema (not a field); activeModel persists
    assert bad.status_code == 200


def test_export_excludes_agent_cache_and_session_store():
    """Exports are the run record, not the agent's private HOME cache
    (tens of MB) or its session store."""
    from app.results.export import _exportable

    assert _exportable(("tasks", "t1", "prompt.md"))
    assert _exportable(("tasks", "t1", "agent-session", "s1", "terminal.log"))
    assert _exportable(("tasks", "t1", "agent-session", "s1", "home", ".copilot",
                        "session-state", "u", "events.jsonl"))
    assert not _exportable(("tasks", "t1", "workspace", "src", "a.py"))
    assert not _exportable(("tasks", "t1", "agent-session", "s1", "home", ".cache",
                            "copilot", "pkg", "app.js"))
    assert not _exportable(("tasks", "t1", "agent-session", "s1", "home", ".copilot",
                            "session-store.db-wal"))


def test_results_csv_shared_by_zip_and_endpoint():
    """One CSV writer, so the ZIP bundle and the endpoints cannot drift."""
    import csv as _csv
    import io as _io

    from app.results.export import results_csv

    tasks = [{"taskKey": "a/b", "status": "failed",
              "result": {"passed": False, "reason": "test_failed", "durationSeconds": 1.5,
                         "agentSeconds": 1.0, "evaluateSeconds": 0.5, "tokensInput": 10,
                         "tokensOutput": 2, "model": "m", "details": {"s": {"ok": False}}}}]
    rows = list(_csv.DictReader(_io.StringIO(results_csv(tasks))))
    assert rows[0]["taskKey"] == "a/b" and rows[0]["reason"] == "test_failed"

    # extra columns (all-runs view) prefix the same shape
    wide = results_csv(tasks, ["runId"], {"runId": "r1"})
    assert wide.splitlines()[0].startswith("runId,taskKey")
    assert wide.splitlines()[1].startswith("r1,a/b")


def test_results_csv_handles_missing_result():
    from app.results.export import results_csv

    text = results_csv([{"taskKey": "t", "status": "queued", "result": None}])
    assert "t,,,,queued" in text


def test_results_csv_carries_analysis_columns():
    """The columns a paper actually needs: spend, context behaviour, test counts."""
    import csv as _csv
    import io as _io

    from app.results.export import results_csv

    task = {
        "taskKey": "commons-io/x", "status": "failed",
        "params": {"project": "commons-io", "refactoringType": "Extract Method"},
        "result": {
            "passed": False, "reason": "compile_test_failed",
            "durationSeconds": 12.0, "agentSeconds": 10.0, "evaluateSeconds": 2.0,
            "model": "free/x", "tokensInput": 1000, "tokensOutput": 100,
            "metrics": {"tokensCacheRead": 400, "tokensReasoning": 30, "contextTokens": 45921,
                        "compactionCount": 2, "contextOverflowCount": 1, "evalIterations": 3},
            "details": {"workspace_changed": {"ok": True},
                        "java_build": {"ok": False, "message": "2029/2032 tests passed.",
                                       "testsPassed": 2029, "testsTotal": 2032}},
        },
    }
    row = next(iter(_csv.DictReader(_io.StringIO(results_csv([task])))))
    assert row["project"] == "commons-io" and row["refactoringType"] == "Extract Method"
    assert row["stagesPassed"] == "1" and row["stagesTotal"] == "2"
    assert row["failedStage"] == "java_build"
    assert row["testsPassed"] == "2029" and row["testsTotal"] == "2032"
    assert row["tokensCacheRead"] == "400" and row["tokensReasoning"] == "30"
    assert row["totalTokens"] == "1100"
    assert row["contextTokens"] == "45921"
    assert row["compactionCount"] == "2" and row["contextOverflowCount"] == "1"
    assert row["evalIterations"] == "3"
    assert row["timedOut"] == "False"


def test_models_endpoint_degrades_without_provider(monkeypatch):
    """Offline or misconfigured provider must not break the wizard — the user
    can still type any model id."""
    from app.api import models as models_api

    models_api._cache.update(at=0.0, models=[])
    monkeypatch.setenv("OPENROUTER_BASE_URL", "")
    out = models_api.list_models()
    assert out["source"] == "unconfigured" and out["models"] == []


def test_models_marks_free_tiers():
    from app.api.models import _is_free

    assert _is_free({"pricing": {"prompt": "0", "completion": "0"}}) is True
    assert _is_free({"pricing": {"prompt": "0.000001", "completion": "0"}}) is False
    assert _is_free({}) is True


def test_probe_strips_ansi_and_banner_lines(monkeypatch):
    """Version banners (maven, gradle) carry ANSI codes and divider lines."""
    import subprocess as sp

    from app.api import system

    monkeypatch.setattr(system.shutil, "which", lambda _c: "/usr/bin/x")
    monkeypatch.setattr(system.subprocess, "run",
                        lambda *a, **k: sp.CompletedProcess(a, 0, "\n------------\n\x1b[1mApache Maven 3.6.3\x1b[m\n", ""))
    assert system._probe(["mvn", "--version"]) == "Apache Maven 3.6.3"

    monkeypatch.setattr(system.shutil, "which", lambda _c: None)
    assert system._probe(["nope"]) == "absent"


@pytest.mark.asyncio
async def test_eval_logs_endpoint_lists_stage_output(client, tmp_env):
    """The Output tab shows build/test output; the engine writes one
    <stage>.log per stage that produced any (dots become underscores)."""
    from app.config import get_settings

    run_id, task_id = "r1", "t1"
    eval_dir = get_settings().outputs_dir / "runs" / run_id / "tasks" / task_id / "eval"
    eval_dir.mkdir(parents=True)
    (eval_dir / "python_tests.log").write_text("Ran 5 tests\nOK\n")
    (eval_dir / "swe_prepare_candidate.log").write_text("prepared\n")

    r = await client.get(f"/api/runs/{run_id}/tasks/{task_id}/logs")
    assert r.status_code == 200
    stages = {l["stage"] for l in r.json()["logs"]}
    assert stages == {"python_tests", "swe_prepare_candidate"}
    assert all(l["sizeBytes"] > 0 for l in r.json()["logs"])


@pytest.mark.asyncio
async def test_eval_logs_endpoint_is_empty_before_evaluation(client):
    r = await client.get("/api/runs/nope/tasks/nope/logs")
    assert r.status_code == 200 and r.json()["logs"] == []


def test_workspace_path_guard_blocks_escape_and_git_internals(tmp_path):
    """The tree hides .git; the file endpoint must not serve it either. And no
    path may leave the workspace."""
    import pytest as _pytest
    from fastapi import HTTPException

    from app.api.runs import _safe_workspace_path

    ws = tmp_path / "workspace"
    (ws / "lib").mkdir(parents=True)
    (ws / "lib" / "a.py").write_text("x = 1\n")
    (ws / ".git").mkdir()
    (ws / ".git" / "config").write_text("[core]\n")

    assert _safe_workspace_path(ws, "lib/a.py").name == "a.py"
    assert _safe_workspace_path(ws, "") == ws.resolve()

    for bad in ["../../etc/passwd", "/etc/passwd", "lib/../../outside"]:
        with _pytest.raises(HTTPException) as exc:
            _safe_workspace_path(ws, bad)
        assert exc.value.status_code == 400

    for git in [".git", ".git/config"]:
        with _pytest.raises(HTTPException) as exc:
            _safe_workspace_path(ws, git)
        assert exc.value.status_code == 403
