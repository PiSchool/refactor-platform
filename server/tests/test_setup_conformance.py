from __future__ import annotations

import asyncio
import csv
import io
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import httpx
import pytest
import yaml
from sqlalchemy import select

from tests.helpers import FIXTURES, make_run, seed_catalog


@pytest.fixture()
async def conformance_client(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    from app import config
    config.get_settings.cache_clear()
    from app.main import app
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.mark.asyncio
async def test_eval_check_fails_closed_for_unknown_run_task(tmp_env, capsys):
    from app.db import engine as db_engine
    from app.evaluation.check import _amain

    await db_engine.migrate()
    code = await _amain("missing-run-task", max_attempts=3)
    output = capsys.readouterr().out

    assert code != 0
    assert "FAILED_STAGE: setup_error" in output
    assert "PASS" not in output


def test_lsp_probe_performs_initialize_handshake(tmp_path):
    from app.execution.lsp import probe_server

    server = FIXTURES / "lsp" / "stublsp" / "server.py"
    ok, detail = probe_server(
        {"command": sys.executable, "args": [str(server)]}, tmp_path, timeout=3,
    )

    assert ok is True, detail
    assert "initialize" in detail.lower()


def test_jdtls_adapter_selects_bundled_java_21(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    module_path = root / "plugins" / "lsp" / "jdtls" / "plugin.py"
    spec = importlib.util.spec_from_file_location("jdtls_test_plugin", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    java_home = tmp_path / "jdk-21"
    java = java_home / "bin" / "java"
    java.parent.mkdir(parents=True)
    java.touch()
    java.chmod(0o755)
    monkeypatch.setenv("JDK_21_HOME", str(java_home))
    real_which = module.shutil.which
    monkeypatch.setattr(
        module.shutil, "which",
        lambda command: "/usr/local/bin/jdtls" if command == "jdtls" else real_which(command),
    )

    plugin = module.Plugin()
    assert plugin.ensure()[0] is True
    config = plugin.server_config(tmp_path)
    assert config["command"].endswith("env")
    assert f"JAVA_HOME={java_home}" in config["args"]
    assert config["args"][-1] == "/usr/local/bin/jdtls"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("setup_key", "counter"),
    [
        ("s1", None),
        ("s1_lsp", "lspActions"),
        ("s1_eval", "evalToolInvocations"),
        ("s3", "subagentInvocations"),
    ],
)
async def test_setup_execution_conformance_matrix(tmp_env, monkeypatch, setup_key, counter):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    temporary_root = tmp_env / "self-check-tmp"
    temporary_root.mkdir()
    monkeypatch.setenv("TMPDIR", str(temporary_root))
    from app import config
    config.get_settings.cache_clear()
    from app.db import engine as db_engine
    from app.db.models import RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    registry = await seed_catalog()
    hub.bind_loop(asyncio.get_running_loop())
    run_id = await make_run(setup_key)
    await execute_run(run_id, registry, hub, RunControl(run_id=run_id))

    async with db_engine.session_factory()() as session:
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == run_id)
        )).scalar_one()
        result = (await session.execute(
            select(TaskResult).where(TaskResult.run_task_id == run_task.id)
        )).scalar_one()

    assert run_task.status == "passed", result.details
    assert result.metrics["setupCompliance"] == "conformant"
    if counter:
        assert result.metrics[counter] > 0
    else:
        for name in ("lspActions", "evalToolInvocations", "subagentInvocations",
                     "retrievalInvocations"):
            assert result.metrics[name] == 0

    if setup_key == "s1_eval":
        checks = Path(result.eval_dir) / "self-checks"
        records = sorted(checks.glob("attempt-*/result.json"))
        assert len(records) == 1
        payload = json.loads(records[0].read_text(encoding="utf-8"))
        assert payload["attempt"] == 1
        assert payload["status"] == "passed", payload
        assert result.metrics["evalAttempts"] == 1
        assert not list(temporary_root.glob("rp-advisory-*"))


@pytest.mark.asyncio
async def test_eval_setup_resumes_once_when_first_pass_ignores_self_check(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    from app import config
    config.get_settings.cache_clear()
    from app.db import engine as db_engine
    from app.db.models import AgentSession, Run, RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    registry = await seed_catalog()
    hub.bind_loop(asyncio.get_running_loop())
    run_id = await make_run("s1_eval")
    async with db_engine.session_factory()() as session:
        run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one()
        run.config = {**run.config, "extra": {"stub_args": ["--skip-eval"]}}
        await session.commit()

    await execute_run(run_id, registry, hub, RunControl(run_id=run_id))

    async with db_engine.session_factory()() as session:
        rt = (await session.execute(select(RunTask).where(RunTask.run_id == run_id))).scalar_one()
        result = (await session.execute(
            select(TaskResult).where(TaskResult.run_task_id == rt.id))).scalar_one()
        agent_session = (await session.execute(
            select(AgentSession).where(AgentSession.run_task_id == rt.id))).scalar_one()

    terminal = Path(agent_session.terminal_path).read_text(encoding="utf-8")
    assert terminal.count("starting agent session") == 2
    assert result.metrics["evalAttempts"] == 1
    assert result.metrics["setupCompliance"] == "conformant"
    assert (Path(agent_session.terminal_path).parents[2] / "eval-compliance-prompt.md").is_file()


def test_setup_assessment_separates_correctness_from_compliance():
    from app.catalog.sdk import SessionInfo
    from app.execution.conformance import assess_setup
    from app.execution.setups import SETUPS

    ignored = assess_setup(SETUPS["s3"], SessionInfo())
    assert ignored.status == "setup_not_exercised"
    assert ignored.conformant is False

    used = assess_setup(SETUPS["s3"], SessionInfo(subagent_invocations=1))
    assert used.status == "conformant"

    contaminated = assess_setup(SETUPS["s1"], SessionInfo(lsp_actions=1))
    assert contaminated.status == "unexpected_capability_use"
    assert contaminated.conformant is False


def test_self_check_attempts_are_capped_and_each_result_is_durable(tmp_path):
    from app.execution import evaltool

    for expected in (1, 2):
        reserved = evaltool.reserve_attempt(tmp_path, max_attempts=2)
        assert reserved is not None
        attempt, attempt_dir = reserved
        assert attempt == expected
        evaltool.write_attempt(attempt_dir, {
            "schemaVersion": 1, "attempt": attempt, "status": "failed", "passed": False,
        })

    assert evaltool.reserve_attempt(tmp_path, max_attempts=2) is None
    root = evaltool.checks_dir(tmp_path)
    assert len(list(root.glob("attempt-*/result.json"))) == 2
    limit = json.loads((root / "limit-reached.json").read_text(encoding="utf-8"))
    assert limit["status"] == "attempt_limit"
    assert limit["maxAttempts"] == 2


def test_missing_lsp_provider_never_degrades_to_s1(tmp_path):
    from app.catalog.loader import Registry
    from app.execution.conformance import SetupUnavailable
    from app.execution.taskloop import _resolve_lsp

    with pytest.raises(SetupUnavailable, match="no LSP plugin"):
        _resolve_lsp(Registry(), "python", tmp_path)


@pytest.mark.asyncio
async def test_lsp_unavailable_is_persisted_as_setup_unavailable(tmp_env):
    from app.db import engine as db_engine
    from app.db.models import RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    registry = await seed_catalog()
    registry.lsp.clear()
    hub.bind_loop(asyncio.get_running_loop())
    run_id = await make_run("s1_lsp")
    await execute_run(run_id, registry, hub, RunControl(run_id=run_id))

    async with db_engine.session_factory()() as session:
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == run_id)
        )).scalar_one()
        result = (await session.execute(
            select(TaskResult).where(TaskResult.run_task_id == run_task.id)
        )).scalar_one()
    assert run_task.status == "error"
    assert result.reason == "setup_unavailable"
    assert result.metrics["setupCompliance"] == "setup_unavailable"


@pytest.mark.asyncio
async def test_self_check_infrastructure_error_invalidates_s1_eval(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    from app import config
    config.get_settings.cache_clear()
    from app.db import engine as db_engine
    from app.db.models import RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    registry = await seed_catalog()
    hub.bind_loop(asyncio.get_running_loop())
    run_id = await make_run(
        "s1_eval", config={"extra": {"stub_args": ["--corrupt-eval"]}},
    )
    await execute_run(run_id, registry, hub, RunControl(run_id=run_id))

    async with db_engine.session_factory()() as session:
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == run_id)
        )).scalar_one()
        result = (await session.execute(
            select(TaskResult).where(TaskResult.run_task_id == run_task.id)
        )).scalar_one()
    assert run_task.status == "error"
    assert result.reason == "setup_unavailable"
    assert result.metrics["setupCompliance"] == "setup_unavailable"
    assert result.metrics["evalAttempts"] == 1


def test_shipped_benchmarks_declare_the_complete_setup_matrix():
    root = Path(__file__).resolve().parents[2]
    expected = {"s1", "s1_lsp", "s1_eval", "s2_rag_naive", "s2_rag_ast", "s3"}
    for benchmark in ("refbench", "swe"):
        manifest = yaml.safe_load((
            root / "plugins" / "benchmarks" / benchmark / "plugin.yaml"
        ).read_text(encoding="utf-8"))
        assert set(manifest["setups"]) == expected
    assert (root / "plugins" / "lsp" / "pylsp" / "plugin.yaml").is_file()
    assert (root / "plugins" / "lsp" / "jdtls" / "plugin.yaml").is_file()


@pytest.mark.asyncio
async def test_create_run_rejects_agent_without_setup_capability(conformance_client, monkeypatch):
    from app.main import app

    catalog = (await conformance_client.get("/api/catalog")).json()
    benchmark = next(b for b in catalog["benchmarks"] if b["key"] == "fixturebench")
    agent = next(a for a in catalog["agents"] if a["key"] == "stub")
    capabilities = app.state.registry.agents["stub"].impl.capabilities
    monkeypatch.setitem(capabilities, "eval_tool", False)

    response = await conformance_client.post("/api/runs", json={
        "benchmarkId": benchmark["id"],
        "setupId": "s1_eval",
        "agentToolId": agent["id"],
        "model": "stub-model",
        "taskKeys": ["fixture-0001"],
        "taskTimeoutSeconds": 30,
    })

    assert response.status_code == 422
    assert "eval_tool" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_driven_setup_matrix_persists_terminal_results_and_exports(
    conformance_client, monkeypatch,
):
    from app.db import engine as db_engine
    from app.db.models import Benchmark
    from app.execution.setups import SETUPS
    from app.retrieval.service import RetrievalResult, RetrievalService

    class _Prepared:
        def prepare(self, request):
            root = request.artifacts_dir / "retrieval"
            root.mkdir(parents=True, exist_ok=True)
            provenance = root / "provenance.json"
            invocations = root / "invocations.jsonl"
            provenance.write_text('{"preInjected": true}', encoding="utf-8")
            invocations.touch()
            return RetrievalResult(
                f"fixture-{request.strategy}", request.strategy,
                "## Retrieved code context\n`target.py` is relevant.\n",
                [{"path": "target.py"}], [{"kind": "broad", "text": request.instructions}],
                True, None, provenance, invocations,
            )

    monkeypatch.setattr(RetrievalService, "from_environment", lambda *_: _Prepared())
    catalog = (await conformance_client.get("/api/catalog")).json()
    benchmark = next(b for b in catalog["benchmarks"] if b["key"] == "fixturebench")
    agent = next(a for a in catalog["agents"] if a["key"] == "stub")
    async with db_engine.session_factory()() as session:
        row = (await session.execute(
            select(Benchmark).where(Benchmark.id == benchmark["id"])
        )).scalar_one()
        row.manifest = {**row.manifest, "setups": list(SETUPS)}
        await session.commit()

    run_ids: dict[str, str] = {}
    for setup_key in SETUPS:
        response = await conformance_client.post("/api/runs", json={
            "benchmarkId": benchmark["id"], "setupId": setup_key,
            "agentToolId": agent["id"], "model": "stub-model",
            "taskKeys": ["fixture-0001"], "taskTimeoutSeconds": 30,
        })
        assert response.status_code == 201, response.text
        run_ids[setup_key] = response.json()["id"]

    for setup_key, run_id in run_ids.items():
        run = None
        for _ in range(200):
            run = (await conformance_client.get(f"/api/runs/{run_id}")).json()
            if run["status"] == "completed":
                break
            await asyncio.sleep(0.05)
        assert run is not None and run["status"] == "completed", (setup_key, run)
        task = run["tasks"][0]
        assert task["status"] == "passed", (setup_key, task)
        assert task["session"]["status"] == "ended"
        assert task["result"]["metrics"]["setupCompliance"] == "conformant"

        exported = await conformance_client.get(f"/api/runs/{run_id}/export")
        assert exported.status_code == 200
        with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
            names = archive.namelist()
            assert "summary.json" in names and "results.csv" in names
            assert any(name.endswith("terminal.log") for name in names)
            rows = list(csv.DictReader(io.StringIO(
                archive.read("results.csv").decode("utf-8")
            )))
            assert rows[0]["setupCompliance"] == "conformant"
            if setup_key == "s1_eval":
                assert any("self-checks/attempt-0001/result.json" in name for name in names)
