from __future__ import annotations

from pydantic import BaseModel, Field


class CreateRun(BaseModel):
    benchmarkId: str
    setupId: str            # setup key (s1|s1_lsp|s1_eval|s3)
    agentToolId: str
    model: str
    taskKeys: list[str] = Field(min_length=1)
    taskTimeoutSeconds: int = 1800


class SettingsUpdate(BaseModel):
    activeModel: str | None = None
    defaultTaskTimeout: int | None = None
    retentionCap: int | None = None
    evalToolMaxAttempts: int | None = None
    keepWorkspace: bool | None = None
    costModel: str | None = None
