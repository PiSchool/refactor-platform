"""Identity-scoped session evidence."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.evidence import artifact_response
from app.db import engine as db_engine
from app.results.artifacts import (
    ArtifactNotFound,
    owned_session,
    ref_dicts,
    resolve_session_artifact,
    session_artifact_refs,
)

router = APIRouter(prefix="/api")

async def _owned(run_id: str, task_id: str, session_id: str):
    async with db_engine.session_factory()() as db:
        try:
            return await owned_session(db, run_id, task_id, session_id)
        except ArtifactNotFound as exc:
            raise HTTPException(404, "unknown session") from exc


@router.get("/runs/{run_id}/tasks/{task_id}/sessions/{session_id}/artifacts")
async def list_session_artifacts(run_id: str, task_id: str, session_id: str):
    session = await _owned(run_id, task_id, session_id)
    return {"artifacts": ref_dicts(session_artifact_refs(run_id, task_id, session))}


@router.get("/runs/{run_id}/tasks/{task_id}/sessions/{session_id}/artifacts/{artifact_key}")
async def session_artifact(
    run_id: str,
    task_id: str,
    session_id: str,
    artifact_key: str,
    download: bool = False,
):
    session = await _owned(run_id, task_id, session_id)
    try:
        artifact = resolve_session_artifact(run_id, task_id, session, artifact_key)
    except ArtifactNotFound as exc:
        raise HTTPException(404, "artifact unavailable") from exc
    return artifact_response(artifact, download=download)
