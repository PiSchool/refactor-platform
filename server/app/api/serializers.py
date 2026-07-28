"""ORM → API JSON (camelCase). Kept in one place so shapes stay consistent."""
from __future__ import annotations
from datetime import timezone

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
from app.config import REPO_ROOT, get_settings
from app.results.artifacts import ref_dicts, session_artifact_refs, task_artifact_refs
from app.results.redaction import public_data

_ACTIVE = {"queued", "running"}


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def _public(value):
    settings = get_settings()
    return public_data(value, (settings.data_dir, settings.outputs_dir, REPO_ROOT))


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
        # Archived study runs carry provenance here; the UI badges them so an
        # imported result is never mistaken for one this instance produced.
        "config": _public(run.config or {}),
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
        "params": _public(task.params),
        "artifacts": ref_dicts(task_artifact_refs(rt.run_id, rt.id)),
        "result": _result(result) if result else None,
        "session": _session(session, rt) if session else None,
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
        "metrics": _public(r.metrics),
        "details": _public(r.details),
    }


def _session(sess: AgentSession, rt: RunTask) -> dict:
    return {
        "id": sess.id,
        "role": "primary",
        "status": sess.status,
        "startedAt": _iso(sess.started_at),
        "finishedAt": _iso(sess.finished_at),
        "artifacts": ref_dicts(session_artifact_refs(rt.run_id, rt.id, sess)),
    }
