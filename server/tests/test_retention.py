"""Automatic artifact pruning must never destroy evidence we cannot recreate.

The cap exists to stop locally executed runs from filling the disk. Imported
study archives are the opposite case: their evidence only exists on disk, so
age must never make them eligible. Active runs are excluded too — their tree
is still being written.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from tests.helpers import FIXTURES, make_run, seed_catalog

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture()
async def catalog(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    await seed_catalog()
    return tmp_env


async def _run_with_evidence(minute: int, *, status: str = "completed",
                             setup_key: str = "s1", config: dict | None = None) -> str:
    from app.config import get_settings
    from app.db import engine as db_engine
    from app.db.models import Run

    run_id = await make_run(setup_key=setup_key, config=config)
    async with db_engine.session_factory()() as session:
        run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one()
        run.status = status
        run.created_at = _EPOCH + timedelta(minutes=minute)
        await session.commit()
    tree = get_settings().outputs_dir / "runs" / run_id / "tasks"
    tree.mkdir(parents=True)
    (tree / "terminal.log").write_text("evidence\n", encoding="utf-8")
    return run_id


async def _set_cap(value: int) -> None:
    from app.db import engine as db_engine
    from app.db.models import RuntimeSetting

    async with db_engine.session_factory()() as session:
        session.add(RuntimeSetting(key="retentionCap", value=value))
        await session.commit()


def _has_evidence(run_id: str) -> bool:
    from app.config import get_settings

    return (get_settings().outputs_dir / "runs" / run_id).is_dir()


@pytest.mark.asyncio
async def test_prune_keeps_newest_runs_and_is_idempotent(catalog):
    from app.results.retention import prune

    await _set_cap(2)
    oldest = await _run_with_evidence(0)
    older = await _run_with_evidence(1)
    newer = await _run_with_evidence(2)
    newest = await _run_with_evidence(3)

    assert sorted(await prune()) == sorted([oldest, older])
    assert not _has_evidence(oldest)
    assert not _has_evidence(older)
    assert _has_evidence(newer)
    assert _has_evidence(newest)
    assert await prune() == []


@pytest.mark.asyncio
async def test_prune_never_deletes_imported_archive_evidence(catalog):
    from app.results.retention import prune

    await _set_cap(1)
    imported = await _run_with_evidence(0, config={"import": {"sourceRunId": "source-run"}})
    archive_setup = await _run_with_evidence(1, setup_key="s3_cao")
    executed = await _run_with_evidence(2)

    assert await prune() == []
    assert _has_evidence(imported)
    assert _has_evidence(archive_setup)
    assert _has_evidence(executed)


@pytest.mark.asyncio
async def test_archives_do_not_consume_the_cap_for_executed_runs(catalog):
    from app.results.retention import prune

    await _set_cap(2)
    archives = [
        await _run_with_evidence(index, config={"import": {"sourceRunId": f"source-{index}"}})
        for index in range(5)
    ]
    kept_older = await _run_with_evidence(10)
    kept_newer = await _run_with_evidence(11)

    assert await prune() == []
    assert all(_has_evidence(run_id) for run_id in [*archives, kept_older, kept_newer])


@pytest.mark.parametrize("status", ["queued", "running"])
@pytest.mark.asyncio
async def test_prune_leaves_active_runs_alone(catalog, status):
    from app.results.retention import prune

    await _set_cap(1)
    active = await _run_with_evidence(0, status=status)
    finished = await _run_with_evidence(1)
    newest = await _run_with_evidence(2)

    assert await prune() == [finished]
    assert _has_evidence(active)
    assert not _has_evidence(finished)
    assert _has_evidence(newest)


@pytest.mark.asyncio
async def test_prune_falls_back_to_the_configured_default_cap(catalog, monkeypatch):
    from app import config
    from app.results.retention import cap, prune

    monkeypatch.setattr(config.get_settings().defaults, "retention_runs_cap", 1)
    assert await cap() == 1

    old = await _run_with_evidence(0)
    kept = await _run_with_evidence(1)

    assert await prune() == [old]
    assert _has_evidence(kept)
