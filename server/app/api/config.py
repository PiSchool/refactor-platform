"""Operator configuration of plugin-provided things.

The plugin manifest stays the source of truth for *what can* run; these
endpoints record the operator's edits (stage tuning, disabled stages/tasks) as
overrides in the DB, which the task loop merges at run time. Nothing here
rewrites a plugin's files.
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
from app.evaluation.engine import effective_pipeline
from app.evaluation.presets import CORE_PRESETS

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
    return {
        "benchmark": key,
        "capture": ev.capture,
        "overridden": bool(override),
        "corePresets": sorted(CORE_PRESETS),
        "pluginStages": sorted(loaded.hooks.stages()) if loaded.hooks else [],
        "shipped": {
            "verify": [{"preset": s.preset, "config": s.config} for s in ev.verify],
            "passed": ev.passed,
        },
        "effective": {
            "verify": [
                {"preset": p, "config": c, "enabled": by_preset.get(p, {}).get("enabled", True)}
                for p, c in verify
            ],
            "passed": passed,
        },
        # stages the plugin ships but the operator disabled
        "disabled": [s.preset for s in ev.verify
                     if by_preset.get(s.preset, {}).get("enabled", True) is False],
    }


@router.put("/benchmarks/{key}/evaluation")
async def put_evaluation(key: str, body: EvaluationEdit, request: Request):
    loaded = _loaded(request, key)
    shipped = {s.preset for s in loaded.manifest.evaluation.verify}
    unknown = [s.preset for s in body.verify if s.preset not in shipped]
    if unknown:
        raise HTTPException(422, f"stages not shipped by this benchmark: {unknown}")
    if body.passed:
        # the expression may only reference stages that will actually run
        from app.evaluation import expressions
        names = {s.preset.split(".")[-1] for s in body.verify if s.enabled} | \
                {s.preset for s in body.verify if s.enabled}
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
