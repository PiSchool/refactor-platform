"""Advisory in-session self-check invoked by eval.sh (S1-eval).

Runs the benchmark's verify pipeline against the agent's live workspace and
prints PASS or a FAILED stage with leak-safe guidance. Benchmark failures exit
0 so the agent can iterate; missing state and infrastructure failures exit 2.
"""
from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.catalog.loader import discover
from app.catalog.sdk import EvalContext
from app.config import get_settings
from app.db import engine as db_engine
from app.evaluation import registry
from app.evaluation.engine import evaluate
from app.execution import evaltool, workspace as ws


def _mutates(loaded) -> bool:
    """Whether scoring would rewrite the workspace the agent is still using.

    Each metric declares it. One that is not installed here is assumed to, since
    running it against the live workspace is the outcome that cannot be undone.
    """
    for stage in loaded.manifest.evaluation.verify:
        metric = registry.get(stage.preset)
        if metric is None or metric.spec.mutates_workspace:
            return True
    return False


def _failed(stage: str, reason: str, guidance: str) -> None:
    print("FAILED")
    print(f"FAILED_STAGE: {stage}")
    print(f"REASON: {reason}")
    print(f"FIX_GUIDANCE: {guidance}")


def _stage_rows(outcome) -> list[dict]:
    return [{
        "name": stage.name,
        "ok": stage.ok,
        "reason": stage.reason,
        "message": stage.message,
        "outputs": stage.outputs,
    } for stage in outcome.stages]


async def _amain(run_task_id: str, max_attempts: int = 3) -> int:
    from sqlalchemy import select

    from app.db.models import RunTask, Task, Benchmark

    settings = get_settings()
    async with db_engine.session_factory()() as session:
        rt = (await session.execute(select(RunTask).where(RunTask.id == run_task_id))).scalar_one_or_none()
        if rt is None:
            _failed("setup_error", "Unknown run task.", "Stop self-checking and report this run as invalid.")
            return 2
        task_artifacts = settings.outputs_dir / "runs" / rt.run_id / "tasks" / rt.id
        reserved = evaltool.reserve_attempt(task_artifacts, max_attempts)
        if reserved is None:
            _failed("attempt_limit", f"Maximum self-check attempts ({max(1, max_attempts)}) reached.",
                    "Stop retrying and finish the task.")
            return 2
        attempt, attempt_dir = reserved

        task_row = (await session.execute(select(Task).where(Task.id == rt.task_id))).scalar_one_or_none()
        bench_row = None if task_row is None else (await session.execute(
            select(Benchmark).where(Benchmark.id == task_row.benchmark_id))).scalar_one_or_none()

    started_at = datetime.now(timezone.utc).isoformat()
    try:
        if not rt.workspace_path:
            raise RuntimeError("Run task has no live workspace.")
        if task_row is None or bench_row is None:
            raise RuntimeError("Run task catalog state is incomplete.")
        registry = discover(settings.plugins_dir)
        loaded = registry.benchmarks.get(bench_row.key)
        if loaded is None:
            raise RuntimeError(f"Benchmark plugin is unavailable: {bench_row.key}")
        task_def = next((t for t in loaded.tasks if t.task_key == task_row.task_key), None)
        if task_def is None:
            raise RuntimeError(f"Task is absent from benchmark plugin: {task_row.task_key}")

        live = Path(rt.workspace_path)
        if not live.is_dir():
            raise RuntimeError("Run task workspace does not exist.")
        diff = ws.capture_diff(live)
        with tempfile.TemporaryDirectory(prefix="rp-advisory-artifacts-") as artifacts_tmp:
            if _mutates(loaded):
                with tempfile.TemporaryDirectory(prefix="rp-advisory-workspace-") as workspace_tmp:
                    workspace = Path(workspace_tmp) / "ws"
                    shutil.copytree(live, workspace)
                    ctx = EvalContext(
                        task=task_def, workspace=workspace, artifacts_dir=Path(artifacts_tmp),
                        data_root=loaded.data_dir, session=None, diff_text=diff, advisory=True,
                    )
                    outcome = evaluate(loaded, ctx)
            else:
                ctx = EvalContext(
                    task=task_def, workspace=live, artifacts_dir=Path(artifacts_tmp),
                    data_root=loaded.data_dir, session=None, diff_text=diff, advisory=True,
                )
                outcome = evaluate(loaded, ctx)
            logs = Path(artifacts_tmp) / "eval"
            if logs.is_dir():
                shutil.copytree(logs, attempt_dir / "logs", dirs_exist_ok=True)
    except Exception as exc:
        payload = {
            "schemaVersion": 1,
            "attempt": attempt,
            "status": "error",
            "passed": False,
            "reason": "setup_error",
            "error": str(exc)[:2000],
            "stages": [],
            "startedAt": started_at,
            "finishedAt": datetime.now(timezone.utc).isoformat(),
        }
        evaltool.write_attempt(attempt_dir, payload)
        _failed("setup_error", payload["error"], "Stop self-checking and report this run as invalid.")
        return 2

    payload = {
        "schemaVersion": 1,
        "attempt": attempt,
        "status": "passed" if outcome.passed else "failed",
        "passed": outcome.passed,
        "reason": outcome.reason,
        "stages": _stage_rows(outcome),
        "startedAt": started_at,
        "finishedAt": datetime.now(timezone.utc).isoformat(),
    }
    evaltool.write_attempt(attempt_dir, payload)

    if outcome.passed:
        print("PASS")
        return 0
    fail = next((s for s in outcome.stages if not s.ok), None)
    _failed(fail.name if fail else "unknown", fail.message if fail else outcome.reason,
            "Address the failing check above and re-run bash eval.sh.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-task", required=True)
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args(argv)
    return asyncio.run(_amain(args.run_task, args.max_attempts))


if __name__ == "__main__":
    sys.exit(main())
