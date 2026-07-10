"""Advisory in-session self-check invoked by eval.sh (S1-eval).

Runs the benchmark's verify pipeline against the agent's live workspace and
prints PASS or a FAILED stage with leak-safe guidance. Always exits 0.
"""
from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

from app.catalog.loader import discover
from app.catalog.sdk import EvalContext
from app.config import get_settings
from app.db import engine as db_engine
from app.evaluation.engine import evaluate
from app.evaluation.presets import CORE_PRESETS
from app.execution import workspace as ws


def _mutates(loaded) -> bool:
    for stage in loaded.manifest.evaluation.verify:
        mod = CORE_PRESETS.get(stage.preset)
        if mod is not None and getattr(mod, "MUTATES_WORKSPACE", False):
            return True
        if "." in stage.preset:  # plugin stages may mutate; be safe
            return True
    return False


async def _amain(run_task_id: str) -> int:
    from sqlalchemy import select

    from app.db.models import RunTask, Task, Benchmark

    settings = get_settings()
    registry = discover(settings.plugins_dir)
    async with db_engine.session_factory()() as session:
        rt = (await session.execute(select(RunTask).where(RunTask.id == run_task_id))).scalar_one_or_none()
        if rt is None or not rt.workspace_path:
            print("PASS")  # nothing to check against
            return 0
        task_row = (await session.execute(select(Task).where(Task.id == rt.task_id))).scalar_one()
        bench_row = (await session.execute(select(Benchmark).where(Benchmark.id == task_row.benchmark_id))).scalar_one()
    loaded = registry.benchmarks.get(bench_row.key)
    if loaded is None:
        print("PASS")
        return 0
    task_def = next((t for t in loaded.tasks if t.task_key == task_row.task_key), None)
    if task_def is None:
        print("PASS")
        return 0

    live = Path(rt.workspace_path)
    diff = ws.capture_diff(live)
    workspace = live
    tmp = None
    if _mutates(loaded):
        tmp = Path(tempfile.mkdtemp(prefix="rp-advisory-"))
        shutil.copytree(live, tmp / "ws", dirs_exist_ok=True)
        workspace = tmp / "ws"
    try:
        ctx = EvalContext(task=task_def, workspace=workspace, artifacts_dir=Path(tempfile.mkdtemp()),
                          data_root=loaded.data_dir, session=None, diff_text=diff, advisory=True)
        outcome = evaluate(loaded, ctx)
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)

    if outcome.passed:
        print("PASS")
        return 0
    fail = next((s for s in outcome.stages if not s.ok), None)
    print("FAILED")
    print(f"FAILED_STAGE: {fail.name if fail else 'unknown'}")
    print(f"REASON: {fail.message if fail else outcome.reason}")
    print("FIX_GUIDANCE: address the failing check above and re-run bash eval.sh.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-task", required=True)
    args = parser.parse_args(argv)
    return asyncio.run(_amain(args.run_task))


if __name__ == "__main__":
    sys.exit(main())
