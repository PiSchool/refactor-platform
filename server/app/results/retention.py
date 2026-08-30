"""Keep DB rows forever; prune artifact blob trees beyond the newest-N cap.

The cap only bounds disk growth from runs this machine executed. Imported
study archives are excluded entirely — their evidence exists nowhere else, so
neither age nor the arrival of newer runs may delete it, and they do not
consume the cap. Unfinished runs are excluded too: their tree is still open.
"""
from __future__ import annotations

import logging
import shutil

from sqlalchemy import select

from app.config import get_settings
from app.db import engine as db_engine
from app.db.models import Run, RuntimeSetting
from app.results.provenance import is_archived_run

logger = logging.getLogger(__name__)

FINISHED_STATUSES = frozenset({"completed", "failed", "stopped"})


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
    prunable = [
        run for run in runs
        if run.status in FINISHED_STATUSES and not is_archived_run(run.config, run.setup_key)
    ]
    pruned = []
    root = get_settings().outputs_dir / "runs"
    for run in prunable[keep:]:
        tree = root / run.id
        if not tree.is_dir():
            continue
        try:
            shutil.rmtree(tree)
        except OSError:
            logger.warning("could not prune artifacts of run %s", run.id, exc_info=True)
            continue
        pruned.append(run.id)
    return pruned
