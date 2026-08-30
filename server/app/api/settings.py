from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.api.schemas import SettingsUpdate
from app.catalog import tools
from app.catalog.bootstrap import bootstrap_error, data_state, start_background_bootstrap_one
from app.config import get_settings, provider_inventory, secret_presence
from app.db import engine as db_engine
from app.db.models import RuntimeSetting
from app.evaluation import metrics

router = APIRouter(prefix="/api")

_EDITABLE = {"activeModel", "defaultTaskTimeout", "retentionCap", "evalToolMaxAttempts", "keepWorkspace", "costModel"}


async def _runtime() -> dict:
    async with db_engine.session_factory()() as s:
        rows = (await s.execute(select(RuntimeSetting))).scalars().all()
        return {r.key: r.value for r in rows}


async def _doc(request: Request) -> dict:
    settings = get_settings()
    rt = await _runtime()
    reg = request.app.state.registry
    return {
        "editable": {
            "activeModel": rt.get("activeModel", settings.defaults.model),
            "defaultTaskTimeout": rt.get("defaultTaskTimeout", settings.defaults.task_timeout_seconds),
            "retentionCap": rt.get("retentionCap", settings.defaults.retention_runs_cap),
            "evalToolMaxAttempts": rt.get("evalToolMaxAttempts", settings.defaults.eval_tool_max_attempts),
            "keepWorkspace": rt.get("keepWorkspace", True),
            # model used for "what would this have cost on X" projections
            "costModel": rt.get("costModel", ""),
        },
        "secrets": secret_presence(),
        # Declared in config.yaml; adding one needs no code change, so the
        # dashboard reads the registry rather than naming a vendor.
        "providers": provider_inventory(),
        "plugins": {
            "benchmarks": [{
                "key": k,
                "name": v.manifest.name,
                "language": v.manifest.language,
                "taskCount": len(v.tasks),
                "dataState": data_state(v),
                "dataError": bootstrap_error(v),
                "setups": v.manifest.setups,
            } for k, v in reg.benchmarks.items()],
            # `command` is the deployment's answer, not the manifest's: whether the
            # declared executable is here and which version it reports.
            "agents": [{"key": k, "name": v.manifest.name,
                        "capabilities": v.impl.capabilities,
                        "available": v.available,
                        "command": tools.command_state(v.manifest)}
                       for k, v in reg.agents.items()],
            # One row per metric: what it measures, whether it can decide a
            # verdict, and whether this deployment can run it at all.
            "metrics": [{**entry, "install": reg.evaluation[entry["id"]].manifest.install}
                        for entry in metrics.catalogue().values()],
            "lsp": [{"key": k, "name": v.manifest.name or k, "language": v.manifest.language,
                     "available": v.impl.ensure()[0]} for k, v in reg.lsp.items()],
        },
        "errors": reg.errors,
    }


@router.post("/benchmarks/{key}/bootstrap")
async def bootstrap_benchmark(key: str, request: Request):
    """Provision a benchmark's data ahead of runs (never at task time)."""
    loaded = request.app.state.registry.benchmarks.get(key)
    if loaded is None:
        raise HTTPException(404, f"unknown benchmark: {key}")
    if data_state(loaded) == "ready":
        return {"key": key, "dataState": "ready"}
    start_background_bootstrap_one(loaded)
    return {
        "key": key,
        "dataState": data_state(loaded),
        "dataError": bootstrap_error(loaded),
    }


@router.get("/settings")
async def get_settings_doc(request: Request):
    return await _doc(request)


@router.put("/settings")
async def put_settings(body: SettingsUpdate, request: Request):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    bad = set(updates) - _EDITABLE
    if bad:
        raise HTTPException(422, f"non-editable keys: {bad}")
    async with db_engine.session_factory()() as s:
        for k, v in updates.items():
            row = (await s.execute(select(RuntimeSetting).where(RuntimeSetting.key == k))).scalar_one_or_none()
            if row is None:
                s.add(RuntimeSetting(key=k, value=v))
            else:
                row.value = v
        await s.commit()
    return await _doc(request)
