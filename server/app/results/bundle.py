"""Pydantic models for the run export manifest.

`manifest.json` is the single accepted archive contract. It identifies when
and from which run an export was produced, which plugins ran it, and a hashed
inventory of every artifact the archive actually contains.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FORMAT = "refactor-platform-run"


class PluginRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    key: str
    name: str


class ArtifactManifestEntry(BaseModel):
    """One archived, sanitized artifact — hash and size cover the exact
    bytes stored in the ZIP, not the original evidence on disk."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    path: str
    size_bytes: int = Field(alias="sizeBytes")
    sha256: str
    media_type: str = Field(alias="mediaType")


class RunManifest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    format: Literal["refactor-platform-run"] = FORMAT
    created_at: datetime = Field(alias="createdAt")
    source_run_id: str = Field(alias="sourceRunId")
    benchmark: PluginRef
    setup: PluginRef
    agent_tool: PluginRef = Field(alias="agentTool")
    status: str
    task_count: int = Field(alias="taskCount")
    artifacts: list[ArtifactManifestEntry] = Field(default_factory=list)


def build_manifest(
    *,
    source_run_id: str,
    benchmark: PluginRef,
    setup: PluginRef,
    agent_tool: PluginRef,
    status: str,
    task_count: int,
    artifacts: list[ArtifactManifestEntry],
    created_at: datetime | None = None,
) -> RunManifest:
    return RunManifest(
        createdAt=created_at or datetime.now(timezone.utc),
        sourceRunId=source_run_id,
        benchmark=benchmark,
        setup=setup,
        agentTool=agent_tool,
        status=status,
        taskCount=task_count,
        artifacts=artifacts,
    )


def export_task_id(ordinal: int) -> str:
    """Export-local, source-anonymized id for a task's archive folder."""
    return f"task-{ordinal:04d}"


def export_session_id(ordinal: int) -> str:
    """Export-local id for a session's archive folder, scoped to its task."""
    return f"session-{ordinal:04d}"
