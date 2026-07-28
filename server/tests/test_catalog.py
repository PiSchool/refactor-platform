from __future__ import annotations

import re
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from helpers import FIXTURES
from sqlalchemy import func, select

from app.catalog.loader import discover


def test_discover_finds_plugins():
    reg = discover(FIXTURES)
    assert "fixturebench" in reg.benchmarks
    assert "stub" in reg.agents
    bench = reg.benchmarks["fixturebench"]
    assert [task.task_key for task in bench.tasks] == ["fixture-0001", "fixture-0002"]
    assert bench.tasks[0].workspace.type == "snapshot"
    assert reg.agents["stub"].impl.capabilities["subagents"] is True


def test_benchmark_bootstrap_is_single_flight_and_observable(tmp_path, monkeypatch):
    """Startup and button-triggered provisioning must never write the same
    benchmark archive concurrently.  While it runs, callers see a real
    provisioning state rather than the previous stale error marker.
    """
    from app.catalog import bootstrap

    entered = threading.Event()
    release = threading.Event()
    calls = 0

    def provision(_data_dir):
        nonlocal calls
        calls += 1
        entered.set()
        assert release.wait(2)

    loaded = SimpleNamespace(
        manifest=SimpleNamespace(key="swe", data=SimpleNamespace(bootstrap="unused.py")),
        data_dir=tmp_path / "swe-data",
    )
    loaded.data_dir.mkdir()
    (loaded.data_dir / ".error").write_text("old corrupt archive\n", encoding="utf-8")
    monkeypatch.setattr(bootstrap, "_bootstrap_fn", lambda _loaded: provision)

    assert bootstrap.start_background_bootstrap_one(loaded) is True
    assert entered.wait(1)
    try:
        assert bootstrap.data_state(loaded) == "provisioning"
        assert bootstrap.start_background_bootstrap_one(loaded) is False
    finally:
        release.set()

    deadline = time.monotonic() + 2
    while bootstrap.data_state(loaded) == "provisioning" and time.monotonic() < deadline:
        time.sleep(0.01)
    assert bootstrap.data_state(loaded) == "ready"
    assert bootstrap.bootstrap_error(loaded) == ""
    assert calls == 1


def test_benchmark_bootstrap_exposes_failure_detail(tmp_path, monkeypatch):
    from app.catalog import bootstrap

    loaded = SimpleNamespace(
        manifest=SimpleNamespace(key="swe-error", data=SimpleNamespace(bootstrap="unused.py")),
        data_dir=tmp_path / "swe-data",
    )
    monkeypatch.setattr(
        bootstrap,
        "_bootstrap_fn",
        lambda _loaded: lambda _data_dir: (_ for _ in ()).throw(RuntimeError("bad ZIP CRC")),
    )

    with pytest.raises(RuntimeError, match="bad ZIP CRC"):
        bootstrap.run_bootstrap(loaded)
    assert bootstrap.data_state(loaded) == "error"
    assert bootstrap.bootstrap_error(loaded) == "bad ZIP CRC"


def test_data_revision_invalidates_a_stale_ready_marker(tmp_path):
    from app.catalog import bootstrap

    loaded = SimpleNamespace(
        manifest=SimpleNamespace(
            key="swe",
            data=SimpleNamespace(bootstrap="unused.py", revision="task-revisions-v1"),
        ),
        data_dir=tmp_path / "swe-data",
    )
    loaded.data_dir.mkdir()
    (loaded.data_dir / ".ready").write_text("ok\n", encoding="utf-8")
    assert bootstrap.data_state(loaded) == "missing"

    (loaded.data_dir / ".ready").write_text("task-revisions-v1\n", encoding="utf-8")
    assert bootstrap.data_state(loaded) == "ready"


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
    # A second sync of the same manifest updates rows rather than adding them.
    assert count == len(reg.benchmarks["fixturebench"].tasks)


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
