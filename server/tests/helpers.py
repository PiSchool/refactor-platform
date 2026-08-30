from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path

from sqlalchemy import select

_FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "plugins"
SHIPPED = Path(__file__).resolve().parents[2] / "plugins"


def _test_deployment() -> Path:
    """A plugins root shaped like a deployment: fixture plugins plus real metrics.

    The fixture benchmark references `git_diff`, `events_metrics` and
    `workspace_changed` the way any benchmark does, and those measurements live in
    `plugins/evaluation/`. Assembling both here runs the tests against the real
    metric implementations without installing anything into the repository: a copy
    under the temporary directory, removed when the process ends.
    """
    root = Path(tempfile.mkdtemp(prefix="rp-test-plugins-"))
    atexit.register(shutil.rmtree, root, True)
    shutil.copytree(_FIXTURE_SOURCE, root, dirs_exist_ok=True)
    for metric in sorted((SHIPPED / "evaluation").iterdir()) if (SHIPPED / "evaluation").is_dir() else []:
        destination = root / "evaluation" / metric.name
        if metric.is_dir() and not destination.exists():
            shutil.copytree(metric, destination,
                            ignore=shutil.ignore_patterns("__pycache__"))
    return root


#: The plugins root the tests load. Not the fixtures directory itself: a test
#: that writes into its deployment must not modify the repository.
FIXTURES = _test_deployment()


def metric(metric_id: str, plugins_dir: Path = SHIPPED):
    """A shipped metric, loaded the way a deployment loads it.

    Tests reach measurements through the plugin loader rather than importing a
    module: that is the path a run takes, and an import that works while the
    plugin does not load would prove nothing.
    """
    from app.catalog.loader import discover
    from app.evaluation import registry

    discover(plugins_dir)
    found = registry.get(metric_id)
    assert found is not None, (
        f"no metric {metric_id!r} under {plugins_dir}; installed: {registry.ids()}")
    return found


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


async def add_second_task(run_id: str) -> str:
    """A run seeds one task; a queue needs more than one."""
    from app.db import engine as db_engine
    from app.db.models import RunTask

    async with db_engine.session_factory()() as s:
        first = (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalar_one()
        second = RunTask(run_id=run_id, task_id=first.task_id, ordinal=1,
                         timeout_seconds=first.timeout_seconds)
        s.add(second)
        await s.commit()
        return second.id


async def task_statuses(run_id: str) -> list[str]:
    from app.db import engine as db_engine
    from app.db.models import RunTask

    async with db_engine.session_factory()() as s:
        rows = (await s.execute(
            select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
        return [row.status for row in rows]


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
        # One task unless the caller names more. The benchmark also ships a task
        # that sleeps, so that the browser suite can stop a run while its agent
        # is working; seeding every task by default would put it in every run.
        tasks = [t for t in tasks if t.task_key in (task_keys or ["fixture-0001"])]
        for i, t in enumerate(tasks):
            s.add(RunTask(run_id=run.id, task_id=t.id, ordinal=i, timeout_seconds=60))
        await s.commit()
        return run.id
