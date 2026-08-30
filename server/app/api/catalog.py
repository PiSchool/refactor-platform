from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import func, select

from app.catalog.bootstrap import bootstrap_error, data_state
from app.db import engine as db_engine
from app.db.models import AgentTool, Benchmark, Task
from app.execution.setups import SETUPS

router = APIRouter(prefix="/api")


@router.get("/catalog")
async def catalog(request: Request):
    reg = request.app.state.registry
    async with db_engine.session_factory()() as s:
        benchmarks = []
        for row in (await s.execute(select(Benchmark))).scalars():
            loaded = reg.benchmarks.get(row.key)
            count = (await s.execute(
                select(func.count()).select_from(Task).where(Task.benchmark_id == row.id))).scalar_one()
            # Read readiness off disk, not off the row: the row is written at
            # startup, and a bootstrap run afterwards would leave it saying
            # "missing" forever while the data sits there.
            state = data_state(loaded) if loaded else row.data_state
            benchmarks.append({
                "id": row.id, "key": row.key, "name": row.name, "language": row.language,
                "taskCount": count, "dataState": state,
                "dataDetail": bootstrap_error(loaded) if loaded else row.data_detail,
                "facets": row.manifest.get("facets", []),
                "setups": row.manifest.get("setups", list(SETUPS)),
            })
        agents = []
        for row in (await s.execute(select(AgentTool))).scalars():
            loaded = reg.agents.get(row.key)
            if loaded is None:
                continue  # a plugin that was removed; don't offer an agent that can't run
            agents.append({
                "id": row.id, "key": row.key, "name": row.name,
                "capabilities": loaded.impl.capabilities,
                "binary": loaded.manifest.binary,
                "available": loaded.available,
                "install": loaded.manifest.install,
            })
    setups = [{"key": k, "name": v.name, "description": v.description,
               "capabilities": {"lsp": v.lsp, "eval_tool": v.eval_tool,
                                "subagents": v.subagents, "retrieval": bool(v.retrieval)}}
              for k, v in SETUPS.items()]
    return {"benchmarks": benchmarks, "agents": agents, "setups": setups}


@router.get("/benchmarks/{benchmark_id}/tasks")
async def benchmark_tasks(benchmark_id: str, includeDisabled: bool = False):
    from app.api.config import disabled_tasks

    async with db_engine.session_factory()() as s:
        bench = (await s.execute(select(Benchmark).where(Benchmark.id == benchmark_id))).scalar_one_or_none()
        if bench is None:
            raise HTTPException(404, "unknown benchmark")
        tasks = (await s.execute(select(Task).where(Task.benchmark_id == bench.id))).scalars().all()
    off = await disabled_tasks(bench.key)
    rows = [{"taskKey": t.task_key, "title": t.title, "params": t.params,
             "disabled": t.task_key in off} for t in tasks]
    if not includeDisabled:
        rows = [r for r in rows if not r["disabled"]]
    return {"tasks": rows, "facets": bench.manifest.get("facets", []), "disabledCount": len(off)}
