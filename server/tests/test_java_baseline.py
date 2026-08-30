from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from tests.helpers import FIXTURES


def _git_workspace(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "Example.java").write_text("class Example {}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-q",
            "-m",
            "baseline",
        ],
        cwd=path,
        check=True,
    )


def _task_def():
    from app.catalog.sdk import TaskDef, WorkspaceSpec

    return TaskDef(
        task_key="java-task",
        title="Java task",
        language="java",
        workspace=WorkspaceSpec(type="snapshot", source="repo"),
        instructions="Refactor Example.",
        params={"compileCommand": "mvn -q -B test", "compileJDK": "17"},
    )


def _stub_metric(monkeypatch, measure):
    """Replace one entry in the metric table for the duration of a test.

    The table is shared process-wide, so it is patched by key rather than
    reassigned: replacing it outright left every later test in the session
    looking at the stub.
    """
    from app.catalog.sdk import EvaluationPlugin
    from app.evaluation import registry

    class _Stub(EvaluationPlugin):
        def measure(self, ctx, config):
            return measure(ctx, config)

    monkeypatch.setitem(
        registry._METRICS, "java_build",
        registry.Metric(id="java_build", impl=_Stub(), plugin_dir=Path("/stub")))


def _loaded_benchmark():
    verify = [
        SimpleNamespace(
            preset="java_build",
            config={
                "command_from": "params.compileCommand",
                "jdk_from": "params.compileJDK",
                "fallback_jdk": 17,
            },
        )
    ]
    return SimpleNamespace(
        manifest=SimpleNamespace(evaluation=SimpleNamespace(verify=verify)),
        data_dir=Path("/unused"),
    )


def test_java_build_timeout_is_a_structured_stage_failure(tmp_path, monkeypatch):
    from app.catalog.sdk import EvalContext

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    context = EvalContext(
        task=_task_def(),
        workspace=workspace,
        artifacts_dir=tmp_path / "artifacts",
        data_root=tmp_path,
        session=None,
        diff_text="",
        advisory=True,
    )

    class _Hung:
        """A build that never returns, then reports nothing after being killed."""

        pid = 2 ** 30                                    # no such process group
        returncode = -9

        def __init__(self, *_args, **_kwargs):
            self.killed = False

        def communicate(self, timeout=None):
            if not self.killed:
                self.killed = True
                raise subprocess.TimeoutExpired(
                    cmd="mvn test", timeout=1, output="partial output\n", stderr="hung\n"
                )
            return "", ""

        def kill(self):
            self.killed = True

    from app.catalog import workspace_commands
    from tests.helpers import metric

    monkeypatch.setattr(workspace_commands.subprocess, "Popen", _Hung)
    result = metric("java_build").measure(context, {"timeout_seconds": 1})

    assert result.ok is False
    assert result.reason == "build_timed_out"
    assert "partial output" in result.log
    assert result.outputs["timedOut"] is True


def test_successful_java_baseline_restores_a_clean_workspace(tmp_path, monkeypatch):
    from app.catalog.sdk import StageResult
    from app.execution.baseline import run_java_baseline
    from app.execution.workspace import status_files

    workspace = tmp_path / "workspace"
    artifacts = tmp_path / "artifacts"
    _git_workspace(workspace)

    def successful_build(ctx, config):
        assert config["timeout_seconds"] == 45
        generated = ctx.workspace / "target" / "generated.class"
        generated.parent.mkdir()
        generated.write_text("generated", encoding="utf-8")
        return StageResult(
            ok=True,
            message="Build+test passed.",
            log="baseline passed\n",
        )

    _stub_metric(monkeypatch, successful_build)
    result = run_java_baseline(
        _loaded_benchmark(), _task_def(), workspace, artifacts, timeout_seconds=45
    )

    assert result is not None and result.ok is True
    assert status_files(workspace) == []
    assert not (workspace / "target").exists()
    assert (artifacts / "eval" / "baseline_java_build.log").read_text() == "baseline passed\n"


async def _java_registry(tmp_path, monkeypatch):
    from app import config
    from app.catalog.loader import discover
    from app.catalog.sync import sync_catalog
    from app.db import engine as db_engine

    # symlinks=True keeps the fixture deployment's installed metrics as links to
    # the shipped ones, which is how a deployment gets java_build here.
    plugins = tmp_path / "plugins"
    shutil.copytree(FIXTURES, plugins, symlinks=True)
    benchmark = plugins / "benchmarks" / "javabench"
    (benchmark / "data" / "repo").mkdir(parents=True)
    (benchmark / "data" / "repo" / "Example.java").write_text(
        "class Example {}\n", encoding="utf-8"
    )
    (benchmark / "plugin.yaml").write_text(
        """type: benchmark
key: javabench
name: Java Fixture
version: 1.0.0
language: java
setups: [s1]
evaluation:
  capture: [git_diff]
  verify:
    - preset: java_build
      config:
        command_from: params.compileCommand
        jdk_from: params.compileJDK
  passed: java_build
""",
        encoding="utf-8",
    )
    (benchmark / "tasks.yaml").write_text(
        """tasks:
  - task_key: java-task
    title: Java task
    workspace: {type: snapshot, source: repo}
    instructions: Refactor Example.
    params: {compileCommand: 'mvn -q -B test', compileJDK: '17'}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("RP_PLUGINS_DIR", str(plugins))
    config.get_settings.cache_clear()
    await db_engine.migrate()
    registry = discover(plugins)
    async with db_engine.session_factory()() as session:
        await sync_catalog(registry, session)
        await session.commit()
    return registry


@pytest.mark.asyncio
async def test_failed_baseline_persists_evidence_without_launching_agent(
    tmp_env, tmp_path, monkeypatch
):
    from app.catalog.sdk import StageResult
    from app.db import engine as db_engine
    from app.db.models import AgentTool, Benchmark, Run, RunTask, Task, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    registry = await _java_registry(tmp_path, monkeypatch)
    async with db_engine.session_factory()() as session:
        benchmark = (
            await session.execute(select(Benchmark).where(Benchmark.key == "javabench"))
        ).scalar_one()
        agent = (
            await session.execute(select(AgentTool).where(AgentTool.key == "stub"))
        ).scalar_one()
        task = (
            await session.execute(
                select(Task).where(
                    Task.benchmark_id == benchmark.id,
                    Task.task_key == "java-task",
                )
            )
        ).scalar_one()
        run = Run(
            benchmark_id=benchmark.id,
            agent_tool_id=agent.id,
            setup_key="s1",
            model="stub-model",
            task_timeout_seconds=60,
        )
        session.add(run)
        await session.flush()
        run_task = RunTask(
            run_id=run.id,
            task_id=task.id,
            ordinal=0,
            timeout_seconds=60,
        )
        session.add(run_task)
        await session.commit()
        run_id, run_task_id = run.id, run_task.id

    def failed_build(_ctx, config):
        assert config["timeout_seconds"] > 0
        return StageResult(
            ok=False,
            reason="compile_test_failed",
            message="Baseline compilation failed.",
            log="baseline compiler error\n",
        )

    _stub_metric(monkeypatch, failed_build)
    prepared = False

    def must_not_prepare(_session):
        nonlocal prepared
        prepared = True
        raise AssertionError("agent must not launch after a failed baseline")

    monkeypatch.setattr(registry.agents["stub"].impl, "prepare", must_not_prepare)
    hub.bind_loop(asyncio.get_running_loop())
    await execute_run(run_id, registry, hub, RunControl(run_id=run_id))

    assert prepared is False
    async with db_engine.session_factory()() as session:
        stored_task = await session.get(RunTask, run_task_id)
        result = (
            await session.execute(
                select(TaskResult).where(TaskResult.run_task_id == run_task_id)
            )
        ).scalar_one()
    assert stored_task.status == "failed"
    assert result.passed is False
    assert result.reason == "baseline_failed"
    assert result.details["baseline"]["reason"] == "compile_test_failed"
    log = (
        tmp_env
        / "data"
        / "outputs"
        / "runs"
        / run_id
        / "tasks"
        / run_task_id
        / "eval"
        / "baseline_java_build.log"
    )
    assert log.read_text(encoding="utf-8") == "baseline compiler error\n"