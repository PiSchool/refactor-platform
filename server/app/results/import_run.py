"""Recreate a run (rows + artifacts) from a platform-exported ZIP."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from app.config import get_settings
from app.db import engine as db_engine
from app.db.models import (
    AgentTool,
    Benchmark,
    Run,
    RunTask,
    Task,
    TaskResult,
    new_id,
    utcnow,
)
from sqlalchemy import select


async def import_zip(data: bytes) -> str:
    import io

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        summary = json.loads(z.read("summary.json"))
        run_id = new_id()
        run_root = get_settings().outputs_dir / "runs" / run_id
        for name in z.namelist():
            if name.startswith("artifacts/") and not name.endswith("/"):
                dest = run_root / Path(name).relative_to("artifacts")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(name))

    run_meta = summary["run"]
    async with db_engine.session_factory()() as s:
        bench = (await s.execute(
            select(Benchmark).where(Benchmark.key == run_meta["benchmark"]["key"]))).scalar_one_or_none()
        tool = (await s.execute(
            select(AgentTool).where(AgentTool.key == run_meta["agentTool"]["key"]))).scalar_one_or_none()
        if bench is None or tool is None:
            raise ValueError("benchmark or agent tool not installed; cannot import")
        run = Run(id=run_id, benchmark_id=bench.id, agent_tool_id=tool.id,
                  setup_key=run_meta["setup"]["key"], model=run_meta["model"], status="completed",
                  config={}, task_timeout_seconds=run_meta.get("taskTimeoutSeconds", 1800),
                  queued_at=utcnow(), finished_at=utcnow(), created_at=utcnow())
        s.add(run)
        await s.flush()
        for t in summary["tasks"]:
            task = (await s.execute(select(Task).where(
                Task.benchmark_id == bench.id, Task.task_key == t["taskKey"]))).scalar_one_or_none()
            if task is None:
                continue
            rt = RunTask(run_id=run.id, task_id=task.id, ordinal=t["ordinal"],
                         status=t["status"], timeout_seconds=t.get("timeoutSeconds", 1800),
                         finished_at=utcnow())
            s.add(rt)
            await s.flush()
            r = t.get("result")
            if r:
                s.add(TaskResult(
                    run_task_id=rt.id, passed=bool(r.get("passed")), reason=r.get("reason") or "",
                    duration_seconds=r.get("durationSeconds") or 0.0,
                    agent_seconds=r.get("agentSeconds") or 0.0,
                    evaluate_seconds=r.get("evaluateSeconds") or 0.0,
                    tokens_input=r.get("tokensInput") or 0, tokens_output=r.get("tokensOutput") or 0,
                    model=r.get("model") or "", metrics=r.get("metrics") or {}, details=r.get("details") or {}))
        await s.commit()
    return run_id
