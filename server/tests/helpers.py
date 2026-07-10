from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

FIXTURES = Path(__file__).parent / "fixtures" / "plugins"


async def seed_catalog():
    from app.catalog.loader import discover
    from app.catalog.sync import sync_catalog
    from app.db import engine as db_engine

    await db_engine.migrate()
    reg = discover(FIXTURES)
    async with db_engine.session_factory()() as s:
        await sync_catalog(reg, s)
        await s.commit()
    return reg


async def make_run(setup_key="s1", config=None, task_keys=None):
    from app.db import engine as db_engine
    from app.db.models import AgentTool, Benchmark, Run, RunTask, Task, utcnow

    async with db_engine.session_factory()() as s:
        bench = (await s.execute(select(Benchmark).where(Benchmark.key == "fixturebench"))).scalar_one()
        tool = (await s.execute(select(AgentTool).where(AgentTool.key == "stub"))).scalar_one()
        run = Run(benchmark_id=bench.id, agent_tool_id=tool.id, setup_key=setup_key,
                  model="stub-model", status="queued", config=config or {},
                  task_timeout_seconds=60, queued_at=utcnow(), created_at=utcnow())
        s.add(run)
        await s.flush()
        tasks = (await s.execute(select(Task).where(Task.benchmark_id == bench.id))).scalars().all()
        if task_keys:
            tasks = [t for t in tasks if t.task_key in task_keys]
        for i, t in enumerate(tasks):
            s.add(RunTask(run_id=run.id, task_id=t.id, ordinal=i, timeout_seconds=60))
        await s.commit()
        return run.id
