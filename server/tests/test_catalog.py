from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import func, select

FIXTURES = Path(__file__).parent / "fixtures" / "plugins"


def test_discover_finds_plugins():
    from app.catalog.loader import discover

    reg = discover(FIXTURES)
    assert "fixturebench" in reg.benchmarks
    assert "stub" in reg.agents
    bench = reg.benchmarks["fixturebench"]
    assert len(bench.tasks) == 1
    assert bench.tasks[0].task_key == "fixture-0001"
    assert bench.tasks[0].workspace.type == "snapshot"
    assert reg.agents["stub"].impl.capabilities["subagents"] is True


def test_invalid_manifest_is_skipped(tmp_path):
    from app.catalog.loader import discover

    bad = tmp_path / "benchmarks" / "broken"
    bad.mkdir(parents=True)
    (bad / "plugin.yaml").write_text("type: benchmark\nkey: broken\n")  # missing required fields
    reg = discover(tmp_path)
    assert "broken" not in reg.benchmarks
    assert any("broken" in e for e in reg.errors)


@pytest.mark.asyncio
async def test_task_upsert_idempotent(tmp_env):
    from app.catalog.loader import discover
    from app.catalog.sync import sync_catalog
    from app.db import engine as db_engine
    from app.db.models import Task

    await db_engine.migrate()
    reg = discover(FIXTURES)
    for _ in range(2):
        async with db_engine.session_factory()() as s:
            await sync_catalog(reg, s)
            await s.commit()
    async with db_engine.session_factory()() as s:
        count = (await s.execute(select(func.count()).select_from(Task))).scalar_one()
    assert count == 1


def test_plugin_import_boundary():
    """Plugin modules may import from app.catalog.sdk only, never app internals."""
    offenders = []
    for py in FIXTURES.rglob("*.py"):
        for m in re.finditer(r"^\s*(?:from|import)\s+(app\.[\w.]+)", py.read_text(), re.M):
            mod = m.group(1)
            if mod != "app.catalog.sdk" and not mod.startswith("app.catalog.sdk"):
                offenders.append(f"{py.name}: {mod}")
    assert not offenders, offenders


async def test_sync_prunes_tasks_removed_from_manifest(tmp_env):
    """A regenerated tasks.yaml must not leave stale keys behind — the catalog
    count silently grew (703 old + 1099 new = 1802) instead of replacing."""
    from sqlalchemy import select

    from app.catalog.sync import sync_catalog
    from app.db import engine as db_engine
    from app.db.models import Task
    from tests.helpers import seed_catalog

    reg = await seed_catalog()
    bench = reg.benchmarks["fixturebench"]
    original = list(bench.tasks)

    async with db_engine.session_factory()() as s:
        before = len((await s.execute(select(Task))).scalars().all())
    assert before == len(original)

    # regenerate with a single, differently-keyed task
    bench.tasks = [original[0]]
    async with db_engine.session_factory()() as s:
        await sync_catalog(reg, s)
        await s.commit()
        keys = {t.task_key for t in (await s.execute(select(Task))).scalars()}
    assert keys == {original[0].task_key}
    bench.tasks = original
