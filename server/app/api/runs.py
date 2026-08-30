from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy import select

from app.api.schemas import CreateRun
from app.api.serializers import run_summary, run_task_detail
from app.config import get_settings
from app.db import engine as db_engine
from app.db.runtime import runtime_value
from app.db.models import AgentTool, Benchmark, Run, RunTask, Task, utcnow
from app.execution.setups import SETUPS
from app.execution.conformance import SetupUnavailable, ensure_agent_compatible
from app.api.evidence import artifact_response
from app.results.artifacts import (
    ArtifactNotFound,
    owned_task,
    ref_dicts,
    resolve_task_artifact,
    task_artifact_refs,
)
from app.results.provenance import is_archived_run
from app.results.redaction import public_data

router = APIRouter(prefix="/api")


@router.get("/runs")
async def list_runs(status: str | None = None, benchmark: str | None = None, setup: str | None = None):
    async with db_engine.session_factory()() as s:
        q = select(Run).order_by(Run.created_at.desc())
        if status:
            q = q.where(Run.status == status)
        if setup:
            q = q.where(Run.setup_key == setup)
        if benchmark:
            b = (await s.execute(select(Benchmark).where(Benchmark.key == benchmark))).scalar_one_or_none()
            if b is None:
                raise HTTPException(400, "unknown benchmark")
            q = q.where(Run.benchmark_id == b.id)
        runs = (await s.execute(q)).scalars().all()
        return {"runs": [await run_summary(r, s) for r in runs]}


@router.post("/runs", status_code=201)
async def create_run(body: CreateRun, request: Request):
    if body.setupId not in SETUPS:
        raise HTTPException(422, f"unknown setup: {body.setupId}")
    async with db_engine.session_factory()() as s:
        bench = (await s.execute(select(Benchmark).where(Benchmark.id == body.benchmarkId))).scalar_one_or_none()
        if bench is None:
            raise HTTPException(422, "unknown benchmark")
        if body.setupId not in bench.manifest.get("setups", list(SETUPS)):
            raise HTTPException(422, "setup not supported by benchmark")
        tool = (await s.execute(select(AgentTool).where(AgentTool.id == body.agentToolId))).scalar_one_or_none()
        if tool is None:
            raise HTTPException(422, "unknown agent tool")
        loaded_agent = request.app.state.registry.agents.get(tool.key)
        if loaded_agent is None:
            raise HTTPException(422, "agent plugin is unavailable")
        if not loaded_agent.available:
            raise HTTPException(422, loaded_agent.unavailable_reason())
        try:
            ensure_agent_compatible(SETUPS[body.setupId], loaded_agent.impl.capabilities)
        except SetupUnavailable as exc:
            raise HTTPException(422, str(exc)) from exc
        tasks = (await s.execute(
            select(Task).where(Task.benchmark_id == bench.id, Task.task_key.in_(body.taskKeys)))).scalars().all()
        found = {t.task_key for t in tasks}
        missing = [k for k in body.taskKeys if k not in found]
        if missing:
            raise HTTPException(422, f"tasks not in benchmark: {missing}")
        if SETUPS[body.setupId].lsp:
            unavailable = sorted({
                task.language for task in tasks
                if request.app.state.registry.lsp_for(task.language) is None
            })
            if unavailable:
                raise HTTPException(422, f"no LSP plugin for task languages: {unavailable}")

        from app.api.config import disabled_tasks
        off = await disabled_tasks(bench.key) & set(body.taskKeys)
        if off:
            raise HTTPException(422, f"tasks disabled in settings: {sorted(off)[:3]}")

        attempts = await runtime_value("evalToolMaxAttempts", get_settings().defaults.eval_tool_max_attempts)
        run = Run(benchmark_id=bench.id, agent_tool_id=tool.id, setup_key=body.setupId,
                  model=body.model, status="queued",
                  config={"eval_tool_max_attempts": attempts},
                  task_timeout_seconds=body.taskTimeoutSeconds, queued_at=utcnow(), created_at=utcnow())
        s.add(run)
        await s.flush()
        by_key = {t.task_key: t for t in tasks}
        for i, key in enumerate(body.taskKeys):
            s.add(RunTask(run_id=run.id, task_id=by_key[key].id, ordinal=i,
                          timeout_seconds=body.taskTimeoutSeconds))
        await s.commit()
        summary = await run_summary(run, s)
    request.app.state.worker.enqueue(summary["id"])
    return summary


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
        if run is None:
            raise HTTPException(404, "unknown run")
        summary = await run_summary(run, s)
        rts = (await s.execute(
            select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
        summary["tasks"] = [await run_task_detail(rt, s) for rt in rts]
        return summary


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str, request: Request):
    ok = await request.app.state.worker.delete_run(run_id)
    if not ok:
        raise HTTPException(409, "run is running or unknown")
    return {"deleted": run_id}


@router.post("/runs/{run_id}/stop")
async def stop_run(run_id: str, request: Request):
    await request.app.state.worker.stop_run(run_id)
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
        if run is None:
            raise HTTPException(404, "unknown run")
        return await run_summary(run, s)


@router.post("/runs/{run_id}/restart", status_code=201)
async def restart_run(run_id: str, request: Request):
    async with db_engine.session_factory()() as s:
        source = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
        if source is None:
            raise HTTPException(404, "unknown run")
        if is_archived_run(source.config, source.setup_key):
            raise HTTPException(422, "archived runs cannot be restarted")
    new_id = await request.app.state.worker.restart_run(run_id)
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == new_id))).scalar_one()
        return await run_summary(run, s)


@router.get("/runs/{run_id}/tasks")
async def list_run_tasks(run_id: str):
    async with db_engine.session_factory()() as s:
        rts = (await s.execute(
            select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
        return {"tasks": [await run_task_detail(rt, s) for rt in rts]}


@router.get("/runs/{run_id}/tasks/{task_id}")
async def get_run_task(run_id: str, task_id: str):
    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.id == task_id, RunTask.run_id == run_id))).scalar_one_or_none()
        if rt is None:
            raise HTTPException(404, "unknown task")
        return await run_task_detail(rt, s)


@router.post("/runs/{run_id}/tasks/{task_id}/skip")
async def skip_task(run_id: str, task_id: str, request: Request):
    await request.app.state.worker.skip_task(run_id, task_id)
    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.id == task_id))).scalar_one_or_none()
        if rt is None:
            raise HTTPException(404, "unknown task")
        return await run_task_detail(rt, s)


@router.post("/runs/import", status_code=201)
async def import_run(file: UploadFile):
    """Stream an uploaded export ZIP to a bounded temp file, then import it.

    The body is never buffered whole in memory: it is copied to a temporary
    file under `outputs/runs` in fixed-size chunks, enforcing the configured
    upload ceiling as it goes. The temp file is always removed, and the
    validated importer works entirely from a `Path`.
    """
    import os
    import tempfile

    from app.results.archive_safety import ArchiveSafetyError, ArchiveTooLarge
    from app.results.import_run import ImportRejected, import_archive

    settings = get_settings()
    limits = settings.import_limits
    runs_dir = settings.outputs_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(prefix=".importing-upload-", suffix=".zip", dir=runs_dir)
    tmp_path = Path(tmp_name)
    try:
        total = 0
        with os.fdopen(fd, "wb") as buffer:
            while chunk := await file.read(limits.chunk_bytes):
                total += len(chunk)
                if total > limits.max_upload_bytes:
                    raise HTTPException(413, "uploaded archive exceeds the size limit")
                buffer.write(chunk)
        try:
            run_id = await import_archive(tmp_path, limits=limits)
        except ArchiveTooLarge as exc:
            raise HTTPException(413, f"import rejected: {exc}") from exc
        except (ImportRejected, ArchiveSafetyError) as exc:
            raise HTTPException(422, f"import failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
        return await run_summary(run, s)


@router.get("/runs/{run_id}/tasks/{task_id}/repo")
async def task_repo_state(run_id: str, task_id: str):
    """Live repository state for a task: the exact checkout the agent is editing.
    Reads the working tree read-only, so it is safe to poll mid-run."""
    from app.execution import workspace as ws

    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(
            RunTask.id == task_id, RunTask.run_id == run_id))).scalar_one_or_none()
        if rt is None:
            raise HTTPException(404, "unknown task")
        task = (await s.execute(select(Task).where(Task.id == rt.task_id))).scalar_one()

    workspace = Path(rt.workspace_path) if rt.workspace_path else None
    state: dict = {
        "taskKey": task.task_key,
        "source": task.workspace.get("source"),
        "ref": task.workspace.get("ref"),
        "live": bool(workspace and workspace.is_dir()),
    }
    if state["live"]:
        try:
            state["baseline"] = ws.head_sha(workspace)
            state["changedFiles"] = ws.status_files(workspace)
        except Exception as exc:  # a mid-write tree must not 500 the page
            state["error"] = str(exc)
    else:
        meta = Path(get_settings().outputs_dir / "runs" / run_id / "tasks" / task_id / "workspace_meta.json")
        if meta.is_file():
            state.update(json.loads(meta.read_text(encoding="utf-8")))
            state["changedFiles"] = [{"status": "M", "path": p} for p in state.get("changedFiles", [])]
    settings = get_settings()
    return public_data(state, (settings.data_dir, settings.outputs_dir))


async def _run_task(run_id: str, task_id: str) -> RunTask:
    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(
            RunTask.id == task_id, RunTask.run_id == run_id))).scalar_one_or_none()
        if rt is None:
            raise HTTPException(404, "unknown task")
        return rt


def _task_dir(run_id: str, task_id: str) -> Path:
    return get_settings().outputs_dir / "runs" / run_id / "tasks" / task_id


def _safe_workspace_path(workspace: Path, rel: str) -> Path:
    """Anything served from a workspace must stay inside it, and never expose
    git internals — the tree hides `.git`, so the file endpoint must too."""
    if "\\" in rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        raise HTTPException(400, "invalid repository-relative path")
    lexical = workspace / rel
    current = workspace
    try:
        for part in Path(rel).parts:
            current = current / part
            if current.is_symlink():
                raise HTTPException(403, "symlinks are not browsable")
    except OSError as exc:
        raise HTTPException(404, "not found") from exc
    target = lexical.resolve()
    root = workspace.resolve()
    if root != target and root not in target.parents:
        raise HTTPException(400, "path outside workspace")
    if ".git" in target.relative_to(root).parts:
        raise HTTPException(403, "git internals are not browsable")
    return target


@router.get("/runs/{run_id}/tasks/{task_id}/diff")
async def task_diff(run_id: str, task_id: str):
    """The agent's delta. Computed live from the workspace while the task runs
    (read-only), and read from the frozen artifact once it is done."""
    from app.execution import workspace as ws

    rt = await _run_task(run_id, task_id)
    workspace = Path(rt.workspace_path) if rt.workspace_path else None
    if workspace and workspace.is_dir():
        try:
            return {"diff": await asyncio.to_thread(ws.live_diff, workspace), "live": True}
        except Exception as exc:  # a tree mid-write must not 500 the page
            return {"diff": "", "live": True, "error": str(exc)}

    artifact = _task_dir(run_id, task_id) / "diff.patch"
    text = artifact.read_text(encoding="utf-8", errors="replace") if artifact.is_file() else ""
    return {"diff": text, "live": False}


_TREE_SKIP = {".git", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", "target", "build"}
_MAX_ENTRIES = 2000


@router.get("/runs/{run_id}/tasks/{task_id}/tree")
async def task_tree(run_id: str, task_id: str, path: str = ""):
    """One directory level of the task's checkout, for file navigation."""
    from app.execution import workspace as ws

    rt = await _run_task(run_id, task_id)
    workspace = Path(rt.workspace_path) if rt.workspace_path else _task_dir(run_id, task_id) / "workspace"
    if not workspace.is_dir():
        return {"entries": [], "changed": [], "available": False}

    base = _safe_workspace_path(workspace, path)
    if not base.is_dir():
        raise HTTPException(404, "not a directory")

    def _listing():
        out = []
        for child in sorted(base.iterdir(), key=lambda c: (c.is_file(), c.name.lower())):
            if child.name in _TREE_SKIP or child.is_symlink():
                continue
            rel = child.relative_to(workspace).as_posix()
            out.append({"name": child.name, "path": rel, "dir": child.is_dir(),
                        "sizeBytes": child.stat().st_size if child.is_file() else 0})
            if len(out) >= _MAX_ENTRIES:
                break
        return out

    entries = await asyncio.to_thread(_listing)
    try:
        changed = await asyncio.to_thread(ws.status_files, workspace)
    except Exception:
        changed = []
    return {"entries": entries, "changed": changed, "available": True}


_MAX_FILE_BYTES = 2_000_000


@router.get("/runs/{run_id}/tasks/{task_id}/file")
async def task_file(run_id: str, task_id: str, path: str):
    rt = await _run_task(run_id, task_id)
    workspace = Path(rt.workspace_path) if rt.workspace_path else _task_dir(run_id, task_id) / "workspace"
    target = _safe_workspace_path(workspace, path)
    if not target.is_file():
        raise HTTPException(404, "not found")
    if target.stat().st_size > _MAX_FILE_BYTES:
        raise HTTPException(413, "file too large to display")

    def _read() -> str:
        return target.read_text(encoding="utf-8", errors="replace")

    return Response(content=await asyncio.to_thread(_read), media_type="text/plain; charset=utf-8")


@router.get("/runs/{run_id}/tasks/{task_id}/artifacts")
async def list_task_artifacts(run_id: str, task_id: str):
    async with db_engine.session_factory()() as session:
        try:
            await owned_task(session, run_id, task_id)
        except ArtifactNotFound as exc:
            raise HTTPException(404, "unknown task") from exc
    return {"artifacts": ref_dicts(task_artifact_refs(run_id, task_id))}


@router.get("/runs/{run_id}/tasks/{task_id}/artifacts/{artifact_key}")
async def task_artifact(
    run_id: str,
    task_id: str,
    artifact_key: str,
    download: bool = False,
):
    async with db_engine.session_factory()() as session:
        try:
            await owned_task(session, run_id, task_id)
        except ArtifactNotFound as exc:
            raise HTTPException(404, "unknown task") from exc
    try:
        artifact = resolve_task_artifact(run_id, task_id, artifact_key)
    except ArtifactNotFound as exc:
        raise HTTPException(404, "artifact unavailable") from exc
    return artifact_response(artifact, download=download)


@router.get("/runs/{run_id}/tasks/{task_id}/logs")
async def task_eval_logs(run_id: str, task_id: str):
    """Build/test output, one entry per evaluation stage that produced any.
    This is the evidence behind a pass/fail — the raw mvn / pytest /
    RefactoringMiner output."""
    async with db_engine.session_factory()() as session:
        try:
            await owned_task(session, run_id, task_id)
        except ArtifactNotFound as exc:
            raise HTTPException(404, "unknown task") from exc
    logs = []
    for ref in task_artifact_refs(run_id, task_id):
        if not ref.key.startswith("eval-log:"):
            continue
        row = ref.model_dump(by_alias=True)
        row["stage"] = ref.key.removeprefix("eval-log:")
        logs.append(row)
    return {"logs": logs}


@router.get("/runs.csv")
async def export_all_runs_csv():
    """Every task of every run, one CSV — the table for offline analysis."""
    from app.results.export import all_runs_csv

    return _csv(await all_runs_csv(), "runs.csv")


@router.get("/runs/{run_id}/export")
async def export_run(run_id: str):
    from app.results.export import build_zip

    path = await build_zip(run_id)
    if path is None:
        raise HTTPException(404, "unknown run")
    return FileResponse(
        path,
        media_type="application/zip",
        filename=f"run-{run_id}.zip",
        background=BackgroundTask(_remove_export_archive, path),
    )


def _remove_export_archive(path: Path) -> None:
    path.unlink(missing_ok=True)
    try:
        path.parent.rmdir()
    except OSError:
        pass


@router.get("/runs/{run_id}/export.csv")
async def export_run_csv(run_id: str):
    from app.results.export import results_csv, run_rows

    rows = await run_rows(run_id)
    if rows is None:
        raise HTTPException(404, "unknown run")
    _, tasks = rows
    return _csv(results_csv(tasks), f"run-{run_id}.csv")


def _csv(text: str, filename: str) -> Response:
    return Response(content=text, media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
