"""Per-run ZIP export: summary.json + results.csv + per-task artifacts."""
from __future__ import annotations

import csv
import io
import json
import tempfile
import zipfile
from pathlib import Path

from sqlalchemy import select

from app.api.serializers import run_summary, run_task_detail
from app.config import get_settings
from app.db import engine as db_engine
from app.db.models import Run, RunTask

#: Analysis columns, in reading order. `details` (a JSON blob of every stage)
#: stays last so a spreadsheet opens on the useful ones.
_CSV_COLS = [
    # identity
    "taskKey", "project", "refactoringType", "mode",
    # verdict
    "status", "passed", "reason", "timedOut",
    # checks
    "stagesPassed", "stagesTotal", "testsPassed", "testsTotal", "failedStage",
    # similarity to the reference refactoring (swe only; blank elsewhere)
    "codebleu", "codebleuSyntax", "codebleuDataflow",
    # timing
    "durationSeconds", "agentSeconds", "evaluateSeconds",
    # model + spend
    "model", "tokensInput", "tokensOutput", "tokensCacheRead", "tokensReasoning",
    "totalTokens", "costUsd",
    # context behaviour
    "contextTokens", "compactionCount", "contextOverflowCount", "evalIterations",
    # raw
    "details",
]

_TIMED_OUT = {"timed_out"}


def _stage_rollup(details: dict) -> dict:
    stages = [(n, v) for n, v in details.items() if isinstance(v, dict) and "ok" in v]
    failed = next((n for n, v in stages if v.get("ok") is False), "")
    return {
        "stagesPassed": sum(1 for _n, v in stages if v.get("ok") is True),
        "stagesTotal": len(stages),
        "failedStage": failed,
    }


def _test_counts(details: dict) -> dict:
    """Counts come from the stage's own outputs, never from re-parsing prose."""
    for stage in details.values():
        if isinstance(stage, dict) and "testsTotal" in stage:
            return {"testsPassed": stage.get("testsPassed", ""), "testsTotal": stage["testsTotal"]}
    return {"testsPassed": "", "testsTotal": ""}


def _cost(result: dict, models: dict) -> float | str:
    from app.api.pricing import cost_usd, usage_from_result

    model = models.get(result.get("model") or "")
    value = cost_usd(usage_from_result(result), (model or {}).get("pricing"))
    return round(value, 6) if value is not None else ""


def _row(task: dict, extra: dict | None = None, models: dict | None = None) -> dict:
    r = task.get("result") or {}
    metrics = r.get("metrics") or {}
    details = r.get("details") or {}
    params = task.get("params") or {}
    models = models or {}

    tin, tout = int(r.get("tokensInput") or 0), int(r.get("tokensOutput") or 0)
    row = {
        "taskKey": task.get("taskKey"),
        "project": params.get("project", ""),
        "refactoringType": params.get("refactoringType", ""),
        "mode": params.get("mode", ""),
        "status": task.get("status"),
        "passed": r.get("passed"),
        "reason": r.get("reason"),
        "timedOut": task.get("status") in _TIMED_OUT,
        **_stage_rollup(details),
        **_test_counts(details),
        "codebleu": metrics.get("codebleu", ""),
        "codebleuSyntax": metrics.get("codebleuSyntax", ""),
        "codebleuDataflow": metrics.get("codebleuDataflow", ""),
        "durationSeconds": r.get("durationSeconds"),
        "agentSeconds": r.get("agentSeconds"),
        "evaluateSeconds": r.get("evaluateSeconds"),
        "model": r.get("model"),
        "tokensInput": tin or "",
        "tokensOutput": tout or "",
        "tokensCacheRead": metrics.get("tokensCacheRead", ""),
        "tokensReasoning": metrics.get("tokensReasoning", ""),
        "totalTokens": (tin + tout) or "",
        "costUsd": _cost(r, models) if r else "",
        "contextTokens": metrics.get("contextTokens", ""),
        "compactionCount": metrics.get("compactionCount", ""),
        "contextOverflowCount": metrics.get("contextOverflowCount", ""),
        "evalIterations": metrics.get("evalIterations", ""),
        "details": json.dumps(details),
    }
    return {**(extra or {}), **row}


def results_csv(tasks: list[dict], extra_cols: list[str] | None = None,
                extra: dict | None = None) -> str:
    """The results table, shared by the ZIP bundle and the CSV endpoints.

    Costs use the provider's live prices; when the catalog is unreachable the
    column is left empty rather than filled with a guess.
    """
    from app.api.models import ensure_catalog

    models = ensure_catalog()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=(extra_cols or []) + _CSV_COLS)
    w.writeheader()
    for t in tasks:
        w.writerow(_row(t, extra, models))
    return buf.getvalue()


async def run_rows(run_id: str) -> tuple[dict, list[dict]] | None:
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
        if run is None:
            return None
        summary = await run_summary(run, s)
        rts = (await s.execute(
            select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
        return summary, [await run_task_detail(rt, s) for rt in rts]


async def all_runs_csv() -> str:
    """Every task of every run — the table you actually analyse in a paper."""
    async with db_engine.session_factory()() as s:
        runs = (await s.execute(select(Run).order_by(Run.queued_at))).scalars().all()
        summaries = [await run_summary(r, s) for r in runs]
    cols = ["runId", "benchmark", "setup", "agentTool"]
    out: list[str] = []
    for i, summary in enumerate(summaries):
        rows = await run_rows(summary["id"])
        if rows is None:
            continue
        _, tasks = rows
        extra = {"runId": summary["id"], "benchmark": summary["benchmark"]["key"],
                 "setup": summary["setup"]["key"], "agentTool": summary["agentTool"]["key"]}
        csv_text = results_csv(tasks, cols, extra)
        out.append(csv_text if i == 0 else csv_text.split("\n", 1)[1])
    return "".join(out) or results_csv([], cols)


async def build_zip(run_id: str) -> Path | None:
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
        if run is None:
            return None
        summary = await run_summary(run, s)
        rts = (await s.execute(
            select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
        tasks = [await run_task_detail(rt, s) for rt in rts]

    run_dir = get_settings().outputs_dir / "runs" / run_id
    tmp = Path(tempfile.mkdtemp(prefix="rp-export-")) / f"run-{run_id}.zip"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("summary.json", json.dumps({"run": summary, "tasks": tasks}, indent=2))
        z.writestr("results.csv", results_csv(tasks))
        # per-task artifacts (whatever survived retention)
        if run_dir.is_dir():
            for path in run_dir.rglob("*"):
                if path.is_file() and _exportable(path.relative_to(run_dir).parts):
                    z.write(path, arcname=str(Path("artifacts") / path.relative_to(run_dir)))
    return tmp


# The agent's private HOME holds its own CLI cache (tens of MB) and a session
# store; neither is part of the run record. Keep the agent-native events log.
_SKIP_DIRS = ("workspace", ".cache")
_SKIP_NAMES = ("session-store.db",)


def _exportable(parts: tuple[str, ...]) -> bool:
    if any(p in _SKIP_DIRS for p in parts):
        return False
    name = parts[-1]
    return not any(name.startswith(s) for s in _SKIP_NAMES)
