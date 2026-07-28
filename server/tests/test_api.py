from __future__ import annotations

import asyncio

import httpx
import pytest
from sqlalchemy import select

from tests.helpers import FIXTURES, make_run


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
    health = (await client.get("/api/health")).json()
    assert health["status"] == "ok"
    assert health["retrieval"]["embeddingModel"]
    assert health["retrieval"]["embeddingsServedBy"]
    cat = (await client.get("/api/catalog")).json()
    assert any(b["key"] == "fixturebench" for b in cat["benchmarks"])
    assert any(a["key"] == "stub" for a in cat["agents"])
    assert {s["key"] for s in cat["setups"]} == {"s1", "s1_lsp", "s1_eval", "s2_rag_naive", "s2_rag_ast", "s3"}


@pytest.mark.asyncio
async def test_system_report_states_the_deployment_not_the_plugins(client):
    """Agent CLIs were listed here and again under the plugins, disagreeing.

    This report probed each agent's command and printed a version beside it,
    while the plugin list printed the version written in the manifest. Two lists
    of the same tools, two different numbers. The report now describes the
    deployment: what it was built from, the toolchain evaluation needs, and the
    retrieval stack. A plugin's command is reported with its plugin.
    """
    doc = (await client.get("/api/system")).json()
    groups = {g["key"]: g for g in doc["groups"]}
    assert list(groups) == ["deployment", "toolchain", "retrieval"]

    assert "Stub Agent" not in str(doc)
    assert "copilot" not in str(doc).lower()

    assert all(r["neededBy"] or r["detail"] for r in groups["toolchain"]["rows"])

    retrieval = {r["name"]: r for r in groups["retrieval"]["rows"]}
    assert retrieval["Model server"]["value"] and retrieval["Model server"]["detail"]
    # The stages a query passes through, in order. There is one retrieval stack,
    # so there is nothing to name but the pipeline and where its models are served.
    assert [r["name"] for r in groups["retrieval"]["rows"]] == [
        "Model server", "Index", "Chunking", "Dense search", "Lexical search",
        "Fusion", "Rerank", "Query expansion",
    ]
    assert all(r["detail"] for r in groups["retrieval"]["rows"])


@pytest.mark.asyncio
async def test_an_agent_tool_is_reported_once_with_the_version_it_answers_with(client):
    """The manifest declared a version nothing kept in step with the CLI.

    The Copilot plugin said 1.0.68 while the image shipped 1.0.75, and a finished
    task recorded the manifest's number as the version that had run. No manifest
    declares a version now; the command is asked.
    """
    plugins = (await client.get("/api/settings")).json()["plugins"]

    assert all("version" not in entry for kind in plugins.values() for entry in kind)

    agent = next(a for a in plugins["agents"] if a["key"] == "stub")
    assert agent["command"]["state"] in {"ok", "absent", "bundled"}
    if agent["command"]["state"] == "absent":
        assert agent["command"]["install"], "an absent command has to say how to install it"
    assert agent["command"]["binary"] or agent["command"]["state"] == "bundled"


@pytest.mark.asyncio
async def test_a_prompt_edit_cannot_drop_the_task_from_the_prompt(client):
    """The editor offered a file name and a text box, and nothing else.

    A template is chosen per task and has values substituted into it. An edit
    that removes one of them produced a prompt with the task missing from it,
    and the run went ahead on it.
    """
    listing = (await client.get("/api/prompts/fixturebench")).json()["prompts"]
    assert listing == [{"name": "task.md", "overridden": False,
                        "appliesTo": "every task in this benchmark", "syntax": "jinja"}]

    doc = (await client.get("/api/prompts/fixturebench/task.md")).json()
    variables = {v["name"]: v for v in doc["variables"]}
    assert variables["task.instructions"] == {
        "name": "task.instructions", "summary": "the task's own instruction text",
        "required": True, "present": True,
    }

    refused = await client.put("/api/prompts/fixturebench/task.md",
                              json={"content": "Refactor something. Good luck.\n"})
    assert refused.status_code == 422
    assert "task.instructions" in refused.json()["detail"]

    kept = await client.put("/api/prompts/fixturebench/task.md",
                            json={"content": "{{ task.instructions }}\nEdit the workspace.\n"})
    assert kept.status_code == 200
    assert (await client.get("/api/prompts/fixturebench/task.md")).json()["overridden"] is True
    assert (await client.delete("/api/prompts/fixturebench/task.md")).status_code == 200


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
    assert all("dataError" in benchmark for benchmark in doc["plugins"]["benchmarks"])
    upd = (await client.put("/api/settings", json={"retentionCap": 5})).json()
    assert upd["editable"]["retentionCap"] == 5
    bad = await client.put("/api/settings", json={"activeModel": "x", "bogus": 1})
    # bogus is ignored by schema (not a field); activeModel persists
    assert bad.status_code == 200


@pytest.mark.asyncio
async def test_benchmark_bootstrap_events_reports_initial_state(client):
    response = await client.get("/api/benchmarks/fixturebench/bootstrap/events")
    assert response.status_code == 200
    assert "event: status" in response.text
    assert '"dataState": "ready"' in response.text


@pytest.mark.asyncio
async def test_benchmark_bootstrap_events_pushes_terminal_state(client, monkeypatch):
    from types import SimpleNamespace

    from app.main import app
    from app.realtime import sse
    from app.realtime.hub import hub

    monkeypatch.setattr(sse, "data_state", lambda _loaded: "provisioning")
    topic = "benchmark:fixturebench"
    previous_subscribers = set(hub._subs.get(topic, ()))
    request = SimpleNamespace(app=app)
    response = await sse.benchmark_bootstrap_events("fixturebench", request)
    stream = response.body_iterator.__aiter__()

    initial = await anext(stream)
    terminal = asyncio.create_task(anext(stream))
    while not set(hub._subs.get(topic, ())).difference(previous_subscribers):
        await asyncio.sleep(0)
    hub.publish(topic, "status", {
        "key": "fixturebench", "dataState": "ready", "dataError": "",
    })
    final = await asyncio.wait_for(terminal, timeout=1)

    assert b'"dataState": "provisioning"' in initial
    assert b'"dataState": "ready"' in final
    with pytest.raises(StopAsyncIteration):
        await anext(stream)
    assert not set(hub._subs.get(topic, ())).difference(previous_subscribers)


def test_export_excludes_agent_cache_and_session_store():
    """Exports are the run record, not the agent's private HOME cache
    (tens of MB) or its session store."""
    from app.results.export import _exportable

    assert _exportable(("tasks", "t1", "prompt.md"))
    assert _exportable(("tasks", "t1", "agent-session", "s1", "terminal.log"))
    assert _exportable(("tasks", "t1", "agent-session", "s1", "home", ".copilot",
                        "session-state", "u", "events.jsonl"))
    assert not _exportable(("tasks", "t1", "workspace", "src", "a.py"))
    assert not _exportable(("tasks", "t1", "agent-session", "s1", "home", ".copilot",
                            "mcp-config.json"))
    assert not _exportable(("tasks", "t1", "agent-session", "s1", "home", ".cache",
                            "copilot", "pkg", "app.js"))
    assert not _exportable(("tasks", "t1", "agent-session", "s1", "home", ".copilot",
                            "session-store.db-wal"))
    for private_name in ("config.json", "session.db", "workspace.yaml", "index.md", "process.log"):
        assert not _exportable(("tasks", "t1", "agent-session", "s1", "home", ".copilot",
                                "session-state", "u", private_name))


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
                        "compactionCount": 2, "contextOverflowCount": 1, "evalIterations": 3,
                        "evalAttempts": 2, "setupCompliance": "conformant",
                        "retrievalPreInjected": True, "retrievalInvocations": 2,
                        "retrievalStrategy": "ast", "retrievalHits": 12,
                        "retrievalQueries": 3,
                        "retrievalIndexKey": "abc123"},
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
    assert row["evalAttempts"] == "2" and row["setupCompliance"] == "conformant"
    assert row["retrievalPreInjected"] == "True"
    assert row["retrievalInvocations"] == "2" and row["retrievalStrategy"] == "ast"
    assert row["retrievalHits"] == "12" and row["retrievalQueries"] == "3"
    assert row["retrievalIndexKey"] == "abc123"
    assert row["timedOut"] == "False"


def test_models_endpoint_degrades_without_provider(monkeypatch):
    """Offline or misconfigured provider must not break the wizard — the user
    can still type any model id."""
    from app.api import models as models_api
    from app.config import ProviderConfig, Settings

    models_api._cache.update(at=0.0, models=[])
    monkeypatch.setattr(models_api, "get_settings",
                        lambda: Settings(providers=[ProviderConfig(key="nowhere")]))
    out = models_api.list_models()
    assert out["source"] == "unconfigured" and out["models"] == []


def test_models_endpoint_does_not_impose_a_free_only_product_policy(monkeypatch):
    """Our validation campaign uses the free router, but the catalog must retain
    every model the configured provider serves that passes the agent filter."""
    from app.api import models as models_api

    models_api._cache.update(at=0.0, models=[])
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://provider.invalid/v1")
    monkeypatch.setattr(models_api, "_fetch", lambda *_: [
        {"id": "openrouter/free", "name": "Free Router", "free": True},
        {"id": "vendor/capable-paid", "name": "Capable Paid", "free": False},
    ])

    out = models_api.list_models(refresh=True)

    assert [model["id"] for model in out["models"]] == [
        "openrouter/free", "vendor/capable-paid",
    ]


def test_models_marks_free_tiers():
    from app.api.models import _is_free

    assert _is_free({"pricing": {"prompt": "0", "completion": "0"}}) is True
    assert _is_free({"pricing": {"prompt": "0.000001", "completion": "0"}}) is False
    assert _is_free({}) is True


def test_probe_strips_ansi_and_banner_lines(monkeypatch):
    """Version banners (maven, gradle) carry ANSI codes and divider lines."""
    import subprocess as sp

    from app.api import system
    from app.catalog import tools

    tools.forget()
    monkeypatch.setattr(tools.shutil, "which", lambda _c: "/usr/bin/x")
    monkeypatch.setattr(tools.subprocess, "run",
                        lambda *a, **k: sp.CompletedProcess(a, 0, "\n------------\n\x1b[1mApache Maven 3.6.3\x1b[m\n", ""))
    assert tools.probe_version("mvn") == "Apache Maven 3.6.3"
    assert system._probe("mvn") == "Apache Maven 3.6.3"

    tools.forget()
    monkeypatch.setattr(tools.shutil, "which", lambda _c: None)
    assert tools.probe_version("nope") == ""
    assert system._probe("nope") == "absent"
    tools.forget()


def test_a_version_row_does_not_repeat_the_tool_name(monkeypatch):
    """`copilot --version` answers `GitHub Copilot CLI 1.0.75.`

    Beside a row already labelled with that name, only the number is
    information, and the trailing full stop is noise.
    """
    import subprocess as sp

    from app.catalog import tools

    tools.forget()
    monkeypatch.setattr(tools.shutil, "which", lambda _c: "/usr/bin/copilot")
    monkeypatch.setattr(tools.subprocess, "run",
                        lambda *a, **k: sp.CompletedProcess(a, 0, "GitHub Copilot CLI 1.0.75.\n", ""))
    assert tools.short_version("copilot", "GitHub Copilot CLI") == "1.0.75"

    tools.forget()
    monkeypatch.setattr(tools.subprocess, "run",
                        lambda *a, **k: sp.CompletedProcess(a, 0, "aider 0.86.2\n", ""))
    assert tools.short_version("aider", "Aider") == "0.86.2"

    # `codex --version` answers `codex-cli 0.145.0`: stripping the executable
    # name off the front left `cli 0.145.0` in the deployment report.
    tools.forget()
    monkeypatch.setattr(tools.subprocess, "run",
                        lambda *a, **k: sp.CompletedProcess(a, 0, "codex-cli 0.145.0\n", ""))
    assert tools.short_version("codex", "OpenAI Codex CLI") == "0.145.0"

    # A tool that answers with no version at all is quoted as it answered.
    tools.forget()
    monkeypatch.setattr(tools.subprocess, "run",
                        lambda *a, **k: sp.CompletedProcess(a, 0, "unknown build\n", ""))
    assert tools.short_version("mytool", "My Tool") == "unknown build"
    tools.forget()


@pytest.mark.asyncio
async def test_eval_logs_endpoint_lists_stage_output(client, tmp_env):
    """The Output tab shows build/test output; the engine writes one
    <stage>.log per stage that produced any (dots become underscores)."""
    from app.config import get_settings
    from app.db import engine as db_engine
    from app.db.models import RunTask

    run_id = await make_run(task_keys=["fixture-0001"])
    async with db_engine.session_factory()() as session:
        task_id = (await session.execute(
            select(RunTask.id).where(RunTask.run_id == run_id)
        )).scalar_one()
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
    from app.db import engine as db_engine
    from app.db.models import RunTask

    run_id = await make_run(task_keys=["fixture-0001"])
    async with db_engine.session_factory()() as session:
        task_id = (await session.execute(
            select(RunTask.id).where(RunTask.run_id == run_id)
        )).scalar_one()

    r = await client.get(f"/api/runs/{run_id}/tasks/{task_id}/logs")
    assert r.status_code == 200 and r.json()["logs"] == []
    assert (await client.get("/api/runs/nope/tasks/nope/logs")).status_code == 404


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
