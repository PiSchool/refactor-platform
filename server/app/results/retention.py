"""Keep DB rows forever; prune artifact blob trees beyond the newest-N cap."""
from __future__ import annotations

import shutil

from sqlalchemy import select

from app.config import get_settings
from app.db import engine as db_engine
from app.db.models import Run, RuntimeSetting


async def cap() -> int:
    async with db_engine.session_factory()() as s:
        row = (await s.execute(select(RuntimeSetting).where(RuntimeSetting.key == "retentionCap"))).scalar_one_or_none()
        if row is not None:
            return int(row.value)
    return get_settings().defaults.retention_runs_cap


async def prune() -> list[str]:
    keep = await cap()
    async with db_engine.session_factory()() as s:
        runs = (await s.execute(select(Run).order_by(Run.created_at.desc()))).scalars().all()
    pruned = []
    root = get_settings().outputs_dir / "runs"
    for run in runs[keep:]:
        tree = root / run.id
        if tree.is_dir():
            shutil.rmtree(tree, ignore_errors=True)
            pruned.append(run.id)
    return pruned
