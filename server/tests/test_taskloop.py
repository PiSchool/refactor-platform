from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select

from tests.helpers import FIXTURES, add_second_task, make_run, seed_catalog, task_statuses


@pytest.mark.asyncio
async def test_task_passes_end_to_end(tmp_env):
    from app.catalog.loader import discover
    from app.db import engine as db_engine
    from app.db.models import RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    reg = await seed_catalog()
    hub.bind_loop(asyncio.get_running_loop())
    run_id = await make_run("s1")
    await execute_run(run_id, reg, hub, RunControl(run_id=run_id))

    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalar_one()
        res = (await s.execute(select(TaskResult).where(TaskResult.run_task_id == rt.id))).scalar_one()
        assert rt.status == "passed", res.details
        assert res.passed is True
        assert res.tokens_input == 100 and res.tokens_output == 50
        assert res.model == "stub-model"


@pytest.mark.asyncio
async def test_a_result_that_cannot_be_recorded_fails_only_its_own_task(tmp_env, monkeypatch):
    """Recording an outcome belongs to the task that produced it.

    When this ran outside the per-task failure boundary, one unwritable result
    aborted the whole run: the tasks behind it never executed and the row stayed
    `running` with no process behind it.
    """
    from app.db import engine as db_engine
    from app.db.models import Run, RunTask, TaskResult
    from app.execution import taskloop
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    reg = await seed_catalog()
    hub.bind_loop(asyncio.get_running_loop())
    run_id = await make_run("s1")
    await add_second_task(run_id)

    record = taskloop._persist
    attempts = {"n": 0}

    async def fails_once(*args, **kwargs):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("the results database went away")
        return await record(*args, **kwargs)

    monkeypatch.setattr(taskloop, "_persist", fails_once)
    await execute_run(run_id, reg, hub, RunControl(run_id=run_id))

    assert await task_statuses(run_id) == ["error", "passed"]
    async with db_engine.session_factory()() as s:
        assert (await s.execute(select(Run).where(Run.id == run_id))).scalar_one().status == "completed"
        first = (await s.execute(select(RunTask).where(
            RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().first()
        result = (await s.execute(select(TaskResult).where(
            TaskResult.run_task_id == first.id))).scalar_one()
        assert result.reason == "result_not_recorded"
        assert result.passed is False
        assert "results database went away" in result.details["error"]


@pytest.mark.asyncio
async def test_an_adapter_that_breaks_the_session_contract_fails_its_task(tmp_env, monkeypatch):
    """A plugin defect is that task's failure, and it names the plugin.

    Unchecked, the wrong type propagates into code that has no idea which
    plugin produced it, and the traceback lands outside the task boundary.
    """
    from app.db import engine as db_engine
    from app.db.models import Run, RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    reg = await seed_catalog()
    hub.bind_loop(asyncio.get_running_loop())
    monkeypatch.setattr(type(reg.agents["stub"].impl), "parse_session",
                        lambda self, events_path, terminal_log_path: {"model": "stub-model"})
    run_id = await make_run("s1")

    await execute_run(run_id, reg, hub, RunControl(run_id=run_id))

    assert await task_statuses(run_id) == ["error"]
    async with db_engine.session_factory()() as s:
        assert (await s.execute(select(Run).where(Run.id == run_id))).scalar_one().status == "completed"
        rt = (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalar_one()
        result = (await s.execute(select(TaskResult).where(
            TaskResult.run_task_id == rt.id))).scalar_one()
        assert "'stub'" in result.details["error"]
        assert "expected SessionInfo" in result.details["error"]


@pytest.mark.asyncio
async def test_timeout_marks_timed_out(tmp_env):
    from app.db import engine as db_engine
    from app.db.models import Run, RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    reg = await seed_catalog()
    hub.bind_loop(asyncio.get_running_loop())
    run_id = await make_run("s1", config={"extra": {"stub_args": ["--sleep", "5"]}})
    # shrink the per-task timeout
    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalar_one()
        rt.timeout_seconds = 1
        await s.commit()
    await execute_run(run_id, reg, hub, RunControl(run_id=run_id))
    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalar_one()
        assert rt.status == "timed_out"
        res = (await s.execute(select(TaskResult).where(TaskResult.run_task_id == rt.id))).scalar_one()
        assert res.reason == "timed_out"
        assert res.passed is False


@pytest.mark.asyncio
async def test_stop_marks_stopped(tmp_env):
    from app.db import engine as db_engine
    from app.db.models import Run, RunTask
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub

    reg = await seed_catalog()
    hub.bind_loop(asyncio.get_running_loop())
    run_id = await make_run("s1", config={"extra": {"stub_args": ["--sleep", "5"]}})
    control = RunControl(run_id=run_id)

    async def stopper():
        await asyncio.sleep(1.0)
        control.stop_event.set()
        from app.execution.pty_host import kill_pid_group
        if control.current_pid:
            kill_pid_group(control.current_pid)

    await asyncio.gather(execute_run(run_id, reg, hub, control), stopper())
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
        rt = (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalar_one()
    assert run.status == "stopped"
    assert rt.status == "stopped"


def test_sandbox_noop_when_unprivileged():
    """On a dev box (non-root) nothing is demoted and no chown is attempted."""
    from app.execution.sandbox import build_user, demote_kwargs

    import os
    if os.geteuid() == 0:
        return  # container path is exercised by the acceptance runs
    assert build_user() is None
    assert demote_kwargs(None) == {}


def test_git_env_marks_workspace_safe():
    """The agent owns the workspace (unprivileged); the platform reads it as
    root. Without safe.directory, `git add -A` aborts with 'dubious ownership'
    and the whole evaluation errors out."""
    from app.execution.workspace import _GIT_ENV

    assert _GIT_ENV["GIT_CONFIG_COUNT"] == "1"
    assert _GIT_ENV["GIT_CONFIG_KEY_0"] == "safe.directory"
    assert _GIT_ENV["GIT_CONFIG_VALUE_0"] == "*"


def test_every_setup_with_capability_has_a_prompt_block():
    """A setup the agent cannot perceive is inert: s1_lsp shipped with no prompt
    block, so 'LSP mode' looked identical to s1 from inside the session."""
    from app.execution.setups import SETUPS

    assert SETUPS["s1"].prompt_block == ""
    for key in ("s1_lsp", "s1_eval", "s3"):
        assert SETUPS[key].prompt_block.strip(), f"{key} has no prompt block"


def test_eval_setup_makes_self_check_mandatory():
    from app.execution.setups import SETUPS

    block = SETUPS["s1_eval"].prompt_block.lower()
    assert "eval.sh" in block
    assert "must" in block
    assert "at least once" in block


def test_retrieval_prompt_describes_usage_without_exposing_implementation():
    from app.execution.setups import SETUPS

    block = SETUPS["s2_rag_ast"].prompt_block

    assert "code retrieval" in block.lower()
    assert "search_codebase" in block
    for internal_term in ("cpu", "s2", "bm25", "reciprocal-rank", "cross-encoder"):
        assert internal_term not in block.lower()


def test_retrieved_context_does_not_expose_execution_device():
    from app.retrieval.models import CodeChunk, SearchHit
    from app.retrieval.service import _render_context

    chunk = CodeChunk("chunk", "module.py", 1, 1, "f", "def f(): pass\n", "python")
    context = _render_context([SearchHit(chunk)], 10_000)

    assert "Retrieved code context" in context
    assert "cpu" not in context.lower()


def test_prompt_artifact_is_exactly_what_the_agent_receives(tmp_path):
    """prompt.md must be the same bytes passed via `-p @prompt.md`."""
    from app.catalog.sdk import SessionCtx, SetupProfile, TaskDef, WorkspaceSpec
    from app.execution.taskloop import _build_prompt

    class _Hooks:
        def build_prompt(self, task, ctx):
            return "BODY"

    class _Manifest:
        prompt = None       # this benchmark builds its prompt in Python

    class _Loaded:
        hooks = _Hooks()
        manifest = _Manifest()

    setup = SetupProfile("s3", "S3", "", subagents=True, prompt_block="BLOCK")
    task = TaskDef("k", "t", "python", WorkspaceSpec("snapshot", "r"), "i", {})
    ctx = SessionCtx(run_id="r", run_task_id="rt", session_id="s", task=task,
                     workspace=tmp_path, artifacts_dir=tmp_path, prompt_path=tmp_path / "prompt.md",
                     config_dir=tmp_path, model="m", setup=setup, requested_env={})
    prompt = _build_prompt(_Loaded(), task, ctx, setup)
    # The benchmark's body and the setup's block are framed by one platform
    # statement of where the repository is; nothing else is added.
    assert prompt == f"Repository root: {tmp_path}\nThat is your working " \
        "directory. Every file path in this task is relative to it.\n\nBODY\n\nBLOCK\n"
    ctx.prompt_path.write_text(prompt, encoding="utf-8")
    assert ctx.prompt_path.read_text(encoding="utf-8") == prompt


def test_platform_scaffolding_is_excluded_from_the_diff(tmp_path):
    """eval.sh / .eval_count / the agent's LSP config land after the baseline
    commit. Without an exclude, `git add -A` sweeps them into diff.patch and
    `workspace_changed` passes on platform files alone."""
    import subprocess

    from app.execution import workspace as ws

    dest = tmp_path / "repo"
    dest.mkdir()
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin"}
    (dest / "code.py").write_text("x = 1\n")
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=dest, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=dest, check=True, env=env)

    # platform scaffolding + a real agent edit
    (dest / "eval.sh").write_text("#!/bin/sh\n")
    (dest / ".eval_count").write_text("1\n")
    (dest / ".github").mkdir()
    (dest / ".github" / "lsp.json").write_text("{}")
    ws.ignore_paths(dest, ["eval.sh", ".eval_count", ".github/lsp.json"])

    assert ws.capture_diff(dest) == "", "scaffolding alone must not register as a change"
    assert ws.changed_files(dest) == []

    (dest / "code.py").write_text("x = 2\n")
    diff = ws.capture_diff(dest)
    assert "code.py" in diff
    assert "eval.sh" not in diff and "lsp.json" not in diff
    assert ws.changed_files(dest) == ["code.py"]


def test_prompt_override_wins_over_shipped_default(tmp_env, tmp_path, monkeypatch):
    """Settings-edited templates live in the data volume so they survive image
    rebuilds, and must take precedence over the plugin's shipped default."""
    from app.catalog.sdk import TaskDef, WorkspaceSpec
    from app.config import get_settings
    from app.execution.taskloop import _template_text

    class _M:
        key = "demo"

    class _Loaded:
        manifest = _M()
        plugin_dir = tmp_path / "plugin"

    (_Loaded.plugin_dir / "prompts").mkdir(parents=True)
    (_Loaded.plugin_dir / "prompts" / "t.md").write_text("SHIPPED")
    assert _template_text(_Loaded(), "prompts/t.md") == "SHIPPED"

    over = get_settings().prompt_overrides_dir / "demo"
    over.mkdir(parents=True)
    (over / "t.md").write_text("EDITED")
    assert _template_text(_Loaded(), "prompts/t.md") == "EDITED"


async def test_events_path_is_published_while_the_agent_runs(tmp_env, tmp_path):
    """The agent names its events file at startup (uuid dir). Until it was
    published mid-run, the live Events view had nothing to read."""
    from sqlalchemy import select

    from app.db import engine as db_engine
    from app.db.models import AgentSession
    from app.execution.taskloop import _track_events_path
    from tests.helpers import make_run, seed_catalog

    await seed_catalog()
    run_id = await make_run()
    async with db_engine.session_factory()() as s:
        rt_id = (await s.execute(select(__import__("app.db.models", fromlist=["RunTask"]).RunTask))).scalars().first().id
        s.add(AgentSession(id="sess1", run_task_id=rt_id, status="running"))
        await s.commit()

    events = tmp_path / "events.jsonl"
    events.write_text('{"type":"session.start"}\n')

    class _Impl:
        def events_path(self, ctx):
            return events

    class _Agent:
        impl = _Impl()

    await _track_events_path("sess1", object(), _Agent())

    async with db_engine.session_factory()() as s:
        sess = (await s.execute(select(AgentSession).where(AgentSession.id == "sess1"))).scalar_one()
        assert sess.events_path == str(events)


async def test_evaluation_does_not_block_the_event_loop(tmp_env, monkeypatch):
    """Evaluation shells out to mvn/pytest for minutes. Run on the event loop it
    froze the ASGI server and the UI saw 'socket hang up'."""
    import asyncio
    import time

    from app.execution import taskloop

    def slow_evaluate(*_a, **_k):
        time.sleep(0.4)  # a stand-in for `mvn clean package`
        return None

    monkeypatch.setattr(taskloop, "_evaluate", slow_evaluate)

    ticks = 0

    async def heartbeat():
        nonlocal ticks
        while True:
            ticks += 1
            await asyncio.sleep(0.02)

    hb = asyncio.create_task(heartbeat())
    await asyncio.to_thread(taskloop._evaluate, None, None, None, None, None, "")
    hb.cancel()

    # a blocked loop would let through ~0 ticks during the 0.4s call
    assert ticks > 5, f"event loop was blocked during evaluation (ticks={ticks})"


def test_live_diff_does_not_touch_the_agents_index(tmp_path):
    """The Diff tab polls mid-run. capture_diff() stages everything with
    `git add -A`; doing that under a working agent would corrupt its index."""
    import subprocess

    from app.execution import workspace as ws

    dest = tmp_path / "repo"
    dest.mkdir()
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin"}
    (dest / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=dest, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=dest, check=True, env=env)

    # agent edits a tracked file and adds an untracked one, staging nothing
    (dest / "a.py").write_text("x = 2\n")
    (dest / "b.py").write_text("y = 1\n")

    diff = ws.live_diff(dest)
    assert "a.py" in diff and "b.py" in diff        # untracked files included
    assert "+x = 2" in diff

    # the real index is untouched: nothing is staged
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=dest,
                            capture_output=True, text=True, env=env).stdout
    assert staged.strip() == "", f"live_diff staged files: {staged!r}"

    # and it matches what capture_diff would produce at the end
    assert ws.live_diff(dest) == ws.capture_diff(dest)


def test_live_diff_respects_platform_excludes(tmp_path):
    import subprocess

    from app.execution import workspace as ws

    dest = tmp_path / "repo"
    dest.mkdir()
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin"}
    (dest / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=dest, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=dest, check=True, env=env)

    (dest / "eval.sh").write_text("#!/bin/sh\n")
    ws.ignore_paths(dest, ["eval.sh"])
    assert ws.live_diff(dest) == ""
