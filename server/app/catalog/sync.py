"""Upsert discovered plugins + their tasks into the DB catalog on startup.

File remains the authoring source; the DB copy gives the wizard queryable
tasks and referential integrity. Idempotent.
"""
from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.bootstrap import data_state
from app.catalog.loader import Registry
from app.db.models import AgentTool, Benchmark, RunTask, Task, utcnow


async def sync_catalog(registry: Registry, session: AsyncSession) -> None:
    for key, loaded in registry.benchmarks.items():
        m = loaded.manifest
        row = (await session.execute(select(Benchmark).where(Benchmark.key == key))).scalar_one_or_none()
        if row is None:
            row = Benchmark(key=key)
            session.add(row)
        row.name = m.name
        row.language = m.language
        row.version = m.version
        row.manifest = m.model_dump(mode="json")
        row.data_state = data_state(loaded)
        row.data_detail = _read_error(loaded)
        row.discovered_at = utcnow()
        await session.flush()
        await _sync_tasks(row, loaded, session)

    for key, loaded in registry.agents.items():
        m = loaded.manifest
        row = (await session.execute(select(AgentTool).where(AgentTool.key == key))).scalar_one_or_none()
        if row is None:
            row = AgentTool(key=key)
            session.add(row)
        row.name = m.name
        row.version = m.version
        row.manifest = m.model_dump(mode="json")


def _read_error(loaded) -> str:
    err = loaded.data_dir / ".error"
    return err.read_text(encoding="utf-8").strip() if err.is_file() else ""


async def _sync_tasks(bench_row: Benchmark, loaded, session: AsyncSession) -> None:
    existing = {
        t.task_key: t
        for t in (await session.execute(select(Task).where(Task.benchmark_id == bench_row.id))).scalars()
    }
    for td in loaded.tasks:
        row = existing.get(td.task_key)
        if row is None:
            row = Task(benchmark_id=bench_row.id, task_key=td.task_key)
            session.add(row)
        row.title = td.title
        row.language = td.language
        row.workspace = asdict(td.workspace)
        row.instructions = td.instructions
        row.params = td.params
    await _prune_tasks(bench_row, {td.task_key for td in loaded.tasks}, existing, session)


async def _prune_tasks(bench_row: Benchmark, current: set[str], existing: dict[str, Task],
                       session: AsyncSession) -> None:
    """Drop tasks the benchmark no longer defines. Without this a regenerated
    tasks.yaml leaves the old keys behind and the catalog count keeps growing.
    Tasks referenced by an existing run are kept so their history stays intact.
    """
    stale = [row for key, row in existing.items() if key not in current]
    if not stale:
        return
    referenced = set((await session.execute(
        select(RunTask.task_id).where(RunTask.task_id.in_([r.id for r in stale]))
    )).scalars())
    for row in stale:
        if row.id not in referenced:
            await session.delete(row)
