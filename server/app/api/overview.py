from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.serializers import run_summary
from app.db import engine as db_engine
from app.db.models import Run

router = APIRouter(prefix="/api")


@router.get("/overview")
async def overview():
    async with db_engine.session_factory()() as s:
        total = (await s.execute(select(func.count()).select_from(Run))).scalar_one()
        active = (await s.execute(
            select(Run).where(Run.status.in_(("queued", "running"))).order_by(Run.queued_at))).scalars().all()
        recent = (await s.execute(select(Run).order_by(Run.created_at.desc()).limit(8))).scalars().all()
        return {
            "runsTotal": total,
            "runningCount": sum(1 for r in active if r.status == "running"),
            "activeRuns": [await run_summary(r, s) for r in active[:4]],
            "recentRuns": [await run_summary(r, s) for r in recent],
        }
