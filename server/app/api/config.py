"""Operator configuration of plugin-provided things.

These endpoints record the operator's edits — a retuned stage, a stage switched
off, a metric added to a pipeline, a task excluded — as overrides in the
database, which the task loop merges at run time. Nothing here rewrites a
plugin's files, so restoring a benchmark to what it ships is one delete.
"""
from __future__ import annotations

import asyncio
import hashlib
import shutil
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.config import get_settings
from app.db import engine as db_engine
from app.db.models import Benchmark, RuntimeSetting, Task
from app.db.runtime import runtime_value
from app.evaluation import metrics, registry
from app.evaluation.engine import effective_pipeline

router = APIRouter(prefix="/api")


# ── helpers ──────────────────────────────────────────────────────────────────

async def _set(key: str, value):
    async with db_engine.session_factory()() as s:
        row = (await s.execute(select(RuntimeSetting).where(RuntimeSetting.key == key))).scalar_one_or_none()
        if value is None:
            if row is not None:
                await s.delete(row)
        elif row is None:
            s.add(RuntimeSetting(key=key, value=value))
        else:
            row.value = value
        await s.commit()


def _loaded(request: Request, key: str):
    loaded = request.app.state.registry.benchmarks.get(key)
    if loaded is None:
        raise HTTPException(404, f"unknown benchmark: {key}")
    return loaded


# ── evaluation pipeline (the "metrics") ──────────────────────────────────────

class StageEdit(BaseModel):
    preset: str
    config: dict = {}
    enabled: bool = True


class EvaluationEdit(BaseModel):
    verify: list[StageEdit] = []
    passed: str = ""


@router.get("/benchmarks/{key}/evaluation")
async def get_evaluation(key: str, request: Request):
    loaded = _loaded(request, key)
    ev = loaded.manifest.evaluation
    override = await runtime_value(f"evaluation:{key}", None)
    verify, passed = effective_pipeline(ev, override)

    by_preset = {s.get("preset"): s for s in (override or {}).get("verify", [])}
    # Each stage is returned with what it measures and the options it accepts, so
    # the operator is not reading metric ids and guessing.
    catalogue = metrics.catalogue()
    prepare = None
    if ev.prepare:
        spec = loaded.hooks.describe_preparation()
        if spec is not None:
            prepare = metrics.preparation(ev.prepare, spec)
    return {
        "benchmark": key,
        "overridden": bool(override),
        # the benchmark's own step, before anything measures
        "prepare": prepare,
        # recorded for every task, never gating
        "capture": [metrics.describe(p, catalogue) for p in ev.capture_ids],
        "shipped": {
            "verify": [{"preset": s.preset, "config": s.config} for s in ev.verify],
            "passed": ev.passed,
        },
        "effective": {
            "verify": [
                {"preset": p, "config": c,
                 "enabled": by_preset.get(p, {}).get("enabled", True),
                 "metric": metrics.describe(p, catalogue)}
                for p, c in verify
            ],
            "passed": passed,
        },
        # every metric installed here, for adding one to this pipeline
        "available": [catalogue[metric_id] for metric_id in sorted(catalogue)],
        # stages the plugin ships but the operator disabled
        "disabled": [s.preset for s in ev.verify
                     if by_preset.get(s.preset, {}).get("enabled", True) is False],
    }


@router.put("/benchmarks/{key}/evaluation")
async def put_evaluation(key: str, body: EvaluationEdit, request: Request):
    loaded = _loaded(request, key)
    # A stage may be one the benchmark ships or any metric installed here: adding
    # `codebleu` to a benchmark that does not mention it needs no plugin edit.
    shipped = {s.preset for s in loaded.manifest.evaluation.verify}
    unknown = [s.preset for s in body.verify
               if s.preset not in shipped and registry.get(s.preset) is None]
    if unknown:
        raise HTTPException(
            422, f"no metric installed for {unknown}; metrics live in plugins/evaluation/")
    recording_only = [s.preset for s in body.verify if s.enabled
                      and (m := registry.get(s.preset)) is not None and not m.spec.gates]
    if recording_only:
        raise HTTPException(
            422, f"{recording_only} only record and cannot fail a task, so they cannot gate")
    if body.passed:
        # the expression may only reference stages that will actually run
        from app.evaluation import expressions
        names = {s.preset for s in body.verify if s.enabled}
        try:
            expressions.evaluate(body.passed, {n: True for n in names})
        except ValueError as exc:
            raise HTTPException(422, f"invalid pass expression: {exc}")
    await _set(f"evaluation:{key}", body.model_dump())
    return await get_evaluation(key, request)


@router.delete("/benchmarks/{key}/evaluation")
async def reset_evaluation(key: str, request: Request):
    _loaded(request, key)
    await _set(f"evaluation:{key}", None)
    return await get_evaluation(key, request)


# ── repositories / mirrors ───────────────────────────────────────────────────

def _mirror_path(source: str) -> Path:
    return get_settings().mirrors_dir / f"{hashlib.sha1(source.encode()).hexdigest()}.git"


def _dir_size(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


@router.get("/benchmarks/{key}/repos")
async def list_repos(key: str, request: Request):
    """The workspace sources this benchmark's tasks check out."""
    loaded = _loaded(request, key)
    counts: dict[tuple[str, str], int] = {}
    for t in loaded.tasks:
        counts[(t.workspace.type, t.workspace.source)] = counts.get((t.workspace.type, t.workspace.source), 0) + 1

    repos = []
    for (wtype, source), n in sorted(counts.items(), key=lambda kv: -kv[1]):
        entry = {"type": wtype, "source": source, "taskCount": n}
        if wtype == "git":
            mirror = _mirror_path(source)
            entry |= {"mirrorPath": str(mirror), "present": mirror.is_dir(),
                      "sizeBytes": await asyncio.to_thread(_dir_size, mirror)}
        else:
            data = loaded.data_dir / source
            entry |= {"mirrorPath": str(data), "present": data.exists(),
                      "sizeBytes": await asyncio.to_thread(_dir_size, data)}
        repos.append(entry)
    return {"benchmark": key, "repos": repos}


class MirrorRequest(BaseModel):
    source: str


def _clone_mirror(source: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    subprocess.run(["git", "clone", "--mirror", source, str(dest)], check=False)


@router.post("/benchmarks/{key}/repos/mirror")
async def mirror_repo(key: str, body: MirrorRequest, request: Request):
    """(Re)clone one source mirror. Data is provisioned ahead of runs."""
    loaded = _loaded(request, key)
    sources = {t.workspace.source for t in loaded.tasks if t.workspace.type == "git"}
    if body.source not in sources:
        raise HTTPException(422, "source is not used by this benchmark")
    dest = _mirror_path(body.source)
    import threading
    threading.Thread(target=_clone_mirror, args=(body.source, dest), daemon=True).start()
    return {"source": body.source, "state": "cloning", "mirrorPath": str(dest)}


# ── task enable / disable ────────────────────────────────────────────────────

class TaskToggle(BaseModel):
    taskKeys: list[str]
    disabled: bool


async def disabled_tasks(benchmark: str) -> set[str]:
    return set(await runtime_value(f"tasks:disabled:{benchmark}", []) or [])


@router.post("/benchmarks/{key}/tasks/disable")
async def toggle_tasks(key: str, body: TaskToggle, request: Request):
    _loaded(request, key)
    async with db_engine.session_factory()() as s:
        bench = (await s.execute(select(Benchmark).where(Benchmark.key == key))).scalar_one_or_none()
        if bench is None:
            raise HTTPException(404, "unknown benchmark")
        known = set((await s.execute(
            select(Task.task_key).where(Task.benchmark_id == bench.id,
                                        Task.task_key.in_(body.taskKeys)))).scalars())
    missing = [k for k in body.taskKeys if k not in known]
    if missing:
        raise HTTPException(422, f"unknown tasks: {missing[:3]}")

    current = await disabled_tasks(key)
    current = current | set(body.taskKeys) if body.disabled else current - set(body.taskKeys)
    await _set(f"tasks:disabled:{key}", sorted(current) or None)
    return {"benchmark": key, "disabled": sorted(current)}
