"""Per-run ZIP export: manifest.json + summary.json + results.csv + per-task artifacts."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path

from sqlalchemy import select

from app.api.serializers import run_summary, run_task_detail
from app.config import REPO_ROOT, get_settings
from app.db import engine as db_engine
from app.db.models import AgentSession, AgentTool, Benchmark, Run, RunTask
from app.results.artifacts import (
    ArtifactNotFound,
    ArtifactTooLarge,
    enforce_size,
    resolve_session_artifact,
    resolve_task_artifact,
    revalidate,
    session_artifact_refs,
    task_artifact_refs,
)
from app.results.bundle import (
    ArtifactManifestEntry,
    PluginRef,
    build_manifest,
    export_session_id,
    export_task_id,
)
from app.results.redaction import Redactor

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
    # setup fidelity: was the setup's mechanism actually exercised?
    "setupCompliance", "setupExercised", "lspActions", "subagentInvocations",
    "evalToolInvocations", "evalAttempts",
    "retrievalPreInjected", "retrievalInvocations", "retrievalStrategy",
    "retrievalHits", "retrievalQueries", "retrievalIndexKey",
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
        "evalAttempts": metrics.get("evalAttempts", ""),
        "setupCompliance": metrics.get("setupCompliance", ""),
        "setupExercised": metrics.get("setupExercised", ""),
        "lspActions": metrics.get("lspActions", ""),
        "subagentInvocations": metrics.get("subagentInvocations", ""),
        "evalToolInvocations": metrics.get("evalToolInvocations", ""),
        "retrievalPreInjected": metrics.get("retrievalPreInjected", ""),
        "retrievalInvocations": metrics.get("retrievalInvocations", ""),
        "retrievalStrategy": metrics.get("retrievalStrategy", ""),
        "retrievalHits": metrics.get("retrievalHits", ""),
        "retrievalQueries": metrics.get("retrievalQueries", ""),
        "retrievalIndexKey": metrics.get("retrievalIndexKey", ""),
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
        bench = (await s.execute(
            select(Benchmark).where(Benchmark.id == run.benchmark_id))).scalar_one()
        tool = (await s.execute(
            select(AgentTool).where(AgentTool.id == run.agent_tool_id))).scalar_one()
        rts = (await s.execute(
            select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
        tasks = [await run_task_detail(rt, s) for rt in rts]
        sessions = (await s.execute(select(AgentSession).where(
            AgentSession.run_task_id.in_([rt.id for rt in rts])
        ))).scalars().all() if rts else []

    settings = get_settings()
    run_dir = settings.outputs_dir / "runs" / run_id
    redactor = Redactor.from_environment(private_paths=(
        run_dir,
        settings.outputs_dir,
        settings.data_dir,
        REPO_ROOT,
    ))

    by_task: dict[str, list[AgentSession]] = {}
    for agent_session in sessions:
        by_task.setdefault(agent_session.run_task_id, []).append(agent_session)

    # Archive folder names and summary ids are export-local: they never leak
    # the source run's live database identifiers into a shared/archived ZIP.
    task_ids = {rt.id: export_task_id(i) for i, rt in enumerate(rts)}
    session_ids = {
        agent_session.id: export_session_id(j)
        for rt in rts
        for j, agent_session in enumerate(by_task.get(rt.id, []))
    }

    tmp = Path(tempfile.mkdtemp(prefix="rp-export-")) / f"run-{run_id}.zip"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        portable = redactor.sanitize({"run": summary, "tasks": tasks}, drop_path_fields=True)
        for i, rt in enumerate(rts):
            portable_task = portable["tasks"][i]
            portable_task["id"] = task_ids[rt.id]
            session_block = portable_task.get("session")
            if session_block is not None:
                live_session_id = (tasks[i].get("session") or {}).get("id")
                if live_session_id in session_ids:
                    session_block["id"] = session_ids[live_session_id]
        z.writestr("summary.json", json.dumps(portable, indent=2))
        z.writestr("results.csv", results_csv(tasks))

        manifest_entries: list[ArtifactManifestEntry] = []
        for rt in rts:
            task_folder = task_ids[rt.id]
            for ref in task_artifact_refs(run_id, rt.id):
                if not ref.available:
                    continue
                try:
                    artifact = resolve_task_artifact(run_id, rt.id, ref.key)
                    enforce_size(artifact, download=True)
                    artifact = revalidate(artifact)
                except (ArtifactNotFound, ArtifactTooLarge):
                    continue
                archive_path = Path("artifacts") / "tasks" / task_folder / artifact.relative_path
                manifest_entries.append(
                    _write_sanitized(z, archive_path, artifact, redactor)
                )

            for agent_session in by_task.get(rt.id, []):
                session_folder = session_ids[agent_session.id]
                for ref in session_artifact_refs(run_id, rt.id, agent_session):
                    if not ref.available:
                        continue
                    try:
                        artifact = resolve_session_artifact(
                            run_id, rt.id, agent_session, ref.key,
                        )
                        enforce_size(artifact, download=True)
                        artifact = revalidate(artifact)
                    except (ArtifactNotFound, ArtifactTooLarge):
                        continue
                    filename = {
                        "terminal": "terminal.log",
                        "transcript": "transcript.txt",
                        "events": "events.jsonl",
                    }[ref.key]
                    archive_path = (
                        Path("artifacts") / "tasks" / task_folder / "sessions"
                        / session_folder / filename
                    )
                    manifest_entries.append(
                        _write_sanitized(z, archive_path, artifact, redactor)
                    )

        manifest = build_manifest(
            source_run_id=run_id,
            benchmark=PluginRef(key=bench.key, name=bench.name),
            setup=PluginRef(
                key=summary["setup"]["key"], name=summary["setup"]["name"],
            ),
            agent_tool=PluginRef(key=tool.key, name=tool.name),
            status=summary["status"],
            task_count=len(rts),
            artifacts=manifest_entries,
        )
        z.writestr(
            "manifest.json",
            json.dumps(manifest.model_dump(mode="json", by_alias=True), indent=2),
        )
    return tmp


def _write_sanitized(
    z: zipfile.ZipFile, archive_path: Path, artifact, redactor: Redactor,
) -> ArtifactManifestEntry:
    """Write transformed evidence directly into the ZIP without a raw copy.

    Hash and size are taken over the sanitized bytes actually stored, not the
    original evidence on disk, so the manifest matches the archive exactly.
    """
    hasher = hashlib.sha256()
    size = 0
    with z.open(archive_path.as_posix(), "w") as target:
        for chunk in redactor.iter_file(
            artifact.path,
            artifact.media_type,
            get_settings().evidence.stream_chunk_bytes,
        ):
            target.write(chunk)
            hasher.update(chunk)
            size += len(chunk)
    return ArtifactManifestEntry(
        path=archive_path.as_posix(),
        sizeBytes=size,
        sha256=hasher.hexdigest(),
        mediaType=artifact.media_type,
    )


# Retained only as a narrow compatibility predicate for callers/tests from the
# v1 exporter. `build_zip` no longer walks the tree: its positive catalog above
# is authoritative.
_SKIP_DIRS = ("workspace", ".cache")
_SKIP_NAMES = ("session-store.db", "mcp-config.json")


def _exportable(parts: tuple[str, ...]) -> bool:
    if any(p in _SKIP_DIRS for p in parts):
        return False
    name = parts[-1]
    if ".copilot" in parts:
        return "session-state" in parts and name == "events.jsonl"
    return not any(name.startswith(s) for s in _SKIP_NAMES)
