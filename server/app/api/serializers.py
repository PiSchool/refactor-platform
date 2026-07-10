"""ORM → API JSON (camelCase). Kept in one place so shapes stay consistent."""
from __future__ import annotations

from datetime import timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AgentSession,
    AgentTool,
    Benchmark,
    Run,
    RunTask,
    Task,
    TaskResult,
)

_ACTIVE = {"queued", "running"}


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat() if dt else None


async def run_summary(run: Run, s: AsyncSession) -> dict:
    bench = (await s.execute(select(Benchmark).where(Benchmark.id == run.benchmark_id))).scalar_one()
    tool = (await s.execute(select(AgentTool).where(AgentTool.id == run.agent_tool_id))).scalar_one()
    from app.execution.setups import SETUPS
    setup = SETUPS.get(run.setup_key)
    rts = (await s.execute(select(RunTask).where(RunTask.run_id == run.id))).scalars().all()
    counts = {"total": len(rts), "passed": 0, "failed": 0, "timedOut": 0, "pending": 0}
    for rt in rts:
        if rt.status == "passed":
            counts["passed"] += 1
        elif rt.status in ("failed", "error", "stopped"):
            counts["failed"] += 1
        elif rt.status == "timed_out":
            counts["timedOut"] += 1
        elif rt.status in ("pending", "running"):
            counts["pending"] += 1
    scored = counts["passed"] + counts["failed"] + counts["timedOut"]
    return {
        "id": run.id,
        "status": run.status,
        "benchmark": {"key": bench.key, "name": bench.name, "language": bench.language},
        "setup": {"key": run.setup_key, "name": setup.name if setup else run.setup_key},
        "agentTool": {"key": tool.key, "name": tool.name},
        "model": run.model,
        "taskTimeoutSeconds": run.task_timeout_seconds,
        "counts": counts,
        "passRate": (counts["passed"] / scored) if scored else 0.0,
        "queuedAt": _iso(run.queued_at),
        "startedAt": _iso(run.started_at),
        "finishedAt": _iso(run.finished_at),
    }


async def run_task_detail(rt: RunTask, s: AsyncSession) -> dict:
    task = (await s.execute(select(Task).where(Task.id == rt.task_id))).scalar_one()
    result = (await s.execute(select(TaskResult).where(TaskResult.run_task_id == rt.id))).scalar_one_or_none()
    session = (await s.execute(select(AgentSession).where(AgentSession.run_task_id == rt.id))).scalars().first()
    return {
        "id": rt.id,
        "taskKey": task.task_key,
        "title": task.title,
        "ordinal": rt.ordinal,
        "status": rt.status,
        "timeoutSeconds": rt.timeout_seconds,
        "startedAt": _iso(rt.started_at),
        "finishedAt": _iso(rt.finished_at),
        "params": task.params,
        # Artifact paths are known from the task directory, so the prompt and
        # diff are viewable while the task is still running — not only after a
        # TaskResult row exists.
        "artifacts": _task_artifacts(rt),
        "result": _result(result) if result else None,
        "session": _session(session) if session else None,
    }


def _task_artifacts(rt: RunTask) -> dict[str, str]:
    from app.config import get_settings

    art = get_settings().outputs_dir / "runs" / rt.run_id / "tasks" / rt.id
    return {
        "prompt": str(art / "prompt.md"),
        "response": str(art / "response.md"),
        "diff": str(art / "diff.patch"),
        "workspaceMeta": str(art / "workspace_meta.json"),
    }


def _result(r: TaskResult) -> dict:
    return {
        "passed": r.passed,
        "reason": r.reason or None,
        "durationSeconds": r.duration_seconds,
        "agentSeconds": r.agent_seconds,
        "evaluateSeconds": r.evaluate_seconds,
        "tokensInput": r.tokens_input,
        "tokensOutput": r.tokens_output,
        "model": r.model,
        "metrics": r.metrics,
        "details": r.details,
        "artifacts": {
            "prompt": r.prompt_path,
            "response": r.response_path,
            "diff": r.diff_path,
            "terminal": r.terminal_path,
            "events": r.events_path,
            "evalDir": r.eval_dir,
            "workspaceMeta": _sibling(r.prompt_path, "workspace_meta.json"),
        },
    }


def _sibling(path: str | None, name: str) -> str | None:
    """Artifacts share one per-task directory; prompt.md anchors it."""
    return str(Path(path).parent / name) if path else None


def _session(sess: AgentSession) -> dict:
    return {
        "id": sess.id,
        "role": "primary",
        "status": sess.status,
        "startedAt": _iso(sess.started_at),
        "finishedAt": _iso(sess.finished_at),
    }
