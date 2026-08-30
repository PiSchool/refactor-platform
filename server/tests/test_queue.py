from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select

from tests.helpers import add_second_task as _add_second_task
from tests.helpers import make_run, seed_catalog
from tests.helpers import task_statuses as _task_statuses


async def _wait_status(run_id, status, timeout=15):
    from app.db import engine as db_engine
    from app.db.models import Run

    for _ in range(int(timeout * 10)):
        async with db_engine.session_factory()() as s:
            run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
            if run.status == status:
                return True
        await asyncio.sleep(0.1)
    return False


@pytest.mark.asyncio
async def test_enqueue_starts_and_second_queues(tmp_env):
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    reg = await seed_catalog()
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        r1 = await make_run("s1", config={"extra": {"stub_args": ["--sleep", "2"]}})
        r2 = await make_run("s1")
        worker.enqueue(r1)
        worker.enqueue(r2)
        # r1 should be running quickly; r2 still queued while r1 runs
        assert await _wait_status(r1, "running", 3)
        from app.db import engine as db_engine
        from app.db.models import Run
        async with db_engine.session_factory()() as s:
            r2row = (await s.execute(select(Run).where(Run.id == r2))).scalar_one()
        assert r2row.status == "queued"
        assert await _wait_status(r1, "completed", 15)
        assert await _wait_status(r2, "completed", 15)
    finally:
        await worker.stop_worker()


@pytest.mark.asyncio
async def test_boot_drain_picks_up_queued(tmp_env):
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    reg = await seed_catalog()
    run_id = await make_run("s1")  # queued before worker starts
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        assert await _wait_status(run_id, "completed", 15)
    finally:
        await worker.stop_worker()


@pytest.mark.asyncio
async def test_restart_clones_into_new_queued(tmp_env):
    from app.db import engine as db_engine
    from app.db.models import RunTask
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    reg = await seed_catalog()
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        r1 = await make_run("s1")
        worker.enqueue(r1)
        assert await _wait_status(r1, "completed", 15)
        r2 = await worker.restart_run(r1)
        assert r2 != r1
        assert await _wait_status(r2, "completed", 15)
        async with db_engine.session_factory()() as s:
            n1 = len((await s.execute(select(RunTask).where(RunTask.run_id == r1))).scalars().all())
            n2 = len((await s.execute(select(RunTask).where(RunTask.run_id == r2))).scalars().all())
        assert n1 == n2 == 1
    finally:
        await worker.stop_worker()


async def _wait_task_running(run_id: str, timeout: float = 10) -> bool:
    for _ in range(int(timeout * 10)):
        if "running" in await _task_statuses(run_id):
            return True
        await asyncio.sleep(0.1)
    return False


@pytest.mark.asyncio
async def test_stop_kills_the_active_task_and_skips_the_remainder(tmp_env):
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    reg = await seed_catalog()
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        run_id = await make_run("s1", config={"extra": {"stub_args": ["--sleep", "30"]}})
        await _add_second_task(run_id)
        worker.enqueue(run_id)
        assert await _wait_task_running(run_id)

        await worker.stop_run(run_id)

        assert await _wait_status(run_id, "stopped", 30)
        assert await _task_statuses(run_id) == ["stopped", "skipped"]
    finally:
        await worker.stop_worker()


@pytest.mark.asyncio
async def test_stop_finalizes_a_queued_run_without_ever_executing_it(tmp_env):
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    reg = await seed_catalog()
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        busy = await make_run("s1", config={"extra": {"stub_args": ["--sleep", "3"]}})
        waiting = await make_run("s1")
        worker.enqueue(busy)
        worker.enqueue(waiting)
        assert await _wait_status(busy, "running", 10)

        await worker.stop_run(waiting)

        assert await _wait_status(waiting, "stopped", 5)
        assert await _task_statuses(waiting) == ["skipped"]
        assert await _wait_status(busy, "completed", 30)
        await asyncio.sleep(0.5)  # the drained queue must not resurrect it
        assert await _task_statuses(waiting) == ["skipped"]
    finally:
        await worker.stop_worker()


@pytest.mark.asyncio
async def test_skipping_a_pending_task_prevents_it_from_running(tmp_env):
    from app.config import get_settings
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    reg = await seed_catalog()
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        run_id = await make_run("s1", config={"extra": {"stub_args": ["--sleep", "3"]}})
        second = await _add_second_task(run_id)
        worker.enqueue(run_id)
        assert await _wait_task_running(run_id)

        await worker.skip_task(run_id, second)

        assert await _wait_status(run_id, "completed", 60)
        assert await _task_statuses(run_id) == ["passed", "skipped"]
        skipped_tree = get_settings().outputs_dir / "runs" / run_id / "tasks" / second
        assert not skipped_tree.exists()
    finally:
        await worker.stop_worker()


@pytest.mark.asyncio
async def test_delete_refuses_an_active_run_and_then_removes_rows_and_blobs(tmp_env):
    from app.config import get_settings
    from app.db import engine as db_engine
    from app.db.models import Run, RunTask
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    reg = await seed_catalog()
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        run_id = await make_run("s1", config={"extra": {"stub_args": ["--sleep", "3"]}})
        worker.enqueue(run_id)
        assert await _wait_task_running(run_id)

        assert await worker.delete_run(run_id) is False

        assert await _wait_status(run_id, "completed", 60)
        tree = get_settings().outputs_dir / "runs" / run_id
        assert tree.is_dir()

        assert await worker.delete_run(run_id) is True

        assert not tree.exists()
        async with db_engine.session_factory()() as s:
            assert (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none() is None
            assert (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalars().all() == []
    finally:
        await worker.stop_worker()


async def test_boot_reconciles_orphaned_running_runs(tmp_env):
    """A restart mid-run must not leave rows stuck in 'running' forever."""
    from app.db import engine as db_engine
    from app.db.models import Run, RunTask
    from app.execution.worker import Worker
    from app.realtime.hub import Hub

    reg = await seed_catalog()
    run_id = await make_run()
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
        run.status = "running"
        rt = (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalars().first()
        rt.status = "running"
        await s.commit()

    await Worker(registry=reg, hub=Hub())._reconcile_orphans()

    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
        rt = (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalars().first()
        assert run.status == "error"
        assert rt.status == "error"


@pytest.mark.asyncio
async def test_startup_closes_tasks_stranded_under_a_finished_run(tmp_env):
    """Rows left open under a run that already ended are repaired on start.

    Reconciliation used to look only at runs still marked `running`, so a task
    orphaned under a finished run stayed open for the life of the database:
    the dashboard showed work in progress under a run that was over.
    """
    from app.db import engine as db_engine
    from app.db.models import Run, RunTask
    from app.execution.worker import Worker
    from app.realtime.hub import Hub

    reg = await seed_catalog()
    run_id = await make_run("s1")
    await _add_second_task(run_id)
    async with db_engine.session_factory()() as s:
        (await s.execute(select(Run).where(Run.id == run_id))).scalar_one().status = "failed"
        rows = (await s.execute(select(RunTask).where(
            RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
        rows[0].status = "running"
        rows[1].status = "pending"
        await s.commit()

    await Worker(registry=reg, hub=Hub())._reconcile_orphans()

    assert await _task_statuses(run_id) == ["error", "skipped"]
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
        assert run.status == "failed"


@pytest.mark.asyncio
async def test_a_crash_outside_the_task_boundary_closes_the_whole_run(tmp_env, monkeypatch):
    """A failure the per-task boundary never saw must still close every row.

    The task has no process behind it once the run is gone. Left as `running`
    it reports work in progress that will never finish and cannot be deleted
    until a restart reconciles it.
    """
    from app.db import engine as db_engine
    from app.db.models import Run, RunTask, utcnow
    from app.execution import worker as worker_mod
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    reg = await seed_catalog()

    async def crash(run_id, registry, hub_, control):
        async with db_engine.session_factory()() as s:
            run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
            run.status = "running"
            rt = (await s.execute(select(RunTask).where(
                RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().first()
            rt.status = "running"
            rt.started_at = utcnow()
            await s.commit()
        raise RuntimeError("execution died where no task could catch it")

    monkeypatch.setattr(worker_mod, "execute_run", crash)
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        run_id = await make_run("s1")
        await _add_second_task(run_id)
        worker.enqueue(run_id)

        assert await _wait_status(run_id, "failed", 15)
        assert await _task_statuses(run_id) == ["error", "skipped"]
    finally:
        await worker.stop_worker()


# --------------------------------------------------------------------------- #
# preparation is visible, and interruptible
# --------------------------------------------------------------------------- #

async def _wait_session(run_id, timeout=15):
    """The session row and its terminal path, as soon as the task has one."""
    from app.db import engine as db_engine
    from app.db.models import AgentSession, RunTask

    for _ in range(int(timeout * 10)):
        async with db_engine.session_factory()() as s:
            row = (await s.execute(
                select(AgentSession).join(RunTask, RunTask.id == AgentSession.run_task_id)
                .where(RunTask.run_id == run_id))).scalars().first()
            if row is not None:
                return row.terminal_path
        await asyncio.sleep(0.1)
    return None


@pytest.mark.asyncio
async def test_preparation_is_visible_before_the_agent_starts(tmp_env, monkeypatch):
    """A task used to show "No session yet" for as long as preparation took.

    Exporting a checkout and building the untouched project take minutes on a
    real Java task, and nothing reported them. The session now exists from the
    first second and each step names itself in the terminal.
    """
    from pathlib import Path

    from app.execution import taskloop
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    real = taskloop.ws.prepare_sync

    def slow(*args, **kwargs):
        import time
        time.sleep(2)
        return real(*args, **kwargs)

    monkeypatch.setattr(taskloop.ws, "prepare_sync", slow)

    reg = await seed_catalog()
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        run_id = await make_run("s1")
        worker.enqueue(run_id)

        terminal_path = await _wait_session(run_id, timeout=10)
        assert terminal_path, "the session must exist while the workspace is being prepared"
        # what the dashboard shows, live and on replay, is the redacted stream
        shown = Path(terminal_path).parent / ".terminal.redacted"
        for _ in range(50):
            text = shown.read_text(encoding="utf-8", errors="replace") if shown.exists() else ""
            if "preparing the workspace" in text:
                break
            await asyncio.sleep(0.1)
        else:                                                   # pragma: no cover
            raise AssertionError("preparation was never announced in the terminal")
        assert await _wait_status(run_id, "completed", 40)
    finally:
        await worker.stop_worker()


@pytest.mark.asyncio
async def test_stop_during_preparation_ends_the_task_without_waiting_for_it(tmp_env, monkeypatch):
    """Stop only killed the agent's pid, which does not exist yet during
    preparation, so the button did nothing until the build had finished."""
    import time

    from app.execution import taskloop
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    entered = asyncio.Event()
    loop = asyncio.get_running_loop()

    def blocks(*_args, **_kwargs):
        loop.call_soon_threadsafe(entered.set)
        time.sleep(60)
        raise AssertionError("preparation should have been abandoned")

    monkeypatch.setattr(taskloop.ws, "prepare_sync", blocks)

    reg = await seed_catalog()
    worker = Worker(registry=reg, hub=hub)
    await worker.start()
    try:
        run_id = await make_run("s1")
        worker.enqueue(run_id)
        await asyncio.wait_for(entered.wait(), timeout=15)

        asked = time.time()
        await worker.stop_run(run_id)
        assert await _wait_status(run_id, "stopped", 15)
        assert time.time() - asked < 10, "stop must not wait for the preparation step"
        assert await _task_statuses(run_id) == ["stopped"]
    finally:
        await worker.stop_worker()
