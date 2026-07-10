from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select

from tests.helpers import make_run, seed_catalog


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
