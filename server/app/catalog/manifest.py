"""plugin.yaml / tasks.yaml schemas (Pydantic-validated at discovery)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SETUP_KEYS = ("s1", "s1_lsp", "s1_eval", "s3")


class FacetSpec(BaseModel):
    key: str
    label: str


class PromptSpec(BaseModel):
    template: str  # path relative to plugin dir, Jinja2 over {task, params}


class DataSpec(BaseModel):
    bootstrap: str = "data_bootstrap.py"


class VerifyStage(BaseModel):
    preset: str
    config: dict[str, Any] = Field(default_factory=dict)


class ArtifactCapture(BaseModel):
    path: str                       # workspace-relative, Jinja2 over {task, params}
    seed: bool = False
    template: str = ""              # inline template text seeded at workspace prep


class EvaluationSpec(BaseModel):
    capture: list[str] = Field(default_factory=list)   # git_diff | file_artifact | events_metrics
    artifact: ArtifactCapture | None = None            # required when capture includes file_artifact
    verify: list[VerifyStage] = Field(default_factory=list)
    passed: str = ""


class DisplaySpec(BaseModel):
    tabs: dict[str, str] = Field(default_factory=dict)


class BenchmarkManifest(BaseModel):
    type: Literal["benchmark"]
    key: str
    name: str
    version: str = "1.0.0"
    language: str
    setups: list[str] = Field(default_factory=lambda: list(SETUP_KEYS))
    facets: list[FacetSpec] = Field(default_factory=list)
    prompt: PromptSpec | None = None
    entrypoint: str = ""            # "plugin:Plugin" when plugin.py present
    data: DataSpec | None = None
    evaluation: EvaluationSpec
    display: DisplaySpec = DisplaySpec()

    @field_validator("setups")
    @classmethod
    def _known_setups(cls, v: list[str]) -> list[str]:
        unknown = [s for s in v if s not in SETUP_KEYS]
        if unknown:
            raise ValueError(f"unknown setups: {unknown}")
        return v


class AgentManifest(BaseModel):
    type: Literal["agent"]
    key: str
    name: str
    version: str = "1.0.0"
    entrypoint: str = "plugin:Plugin"
    capabilities: dict[str, bool] = Field(default_factory=dict)
    models: list[str] = Field(default_factory=list)


class LspManifest(BaseModel):
    type: Literal["lsp"]
    key: str
    name: str = ""
    language: str
    entrypoint: str = "plugin:Plugin"


class TaskEntry(BaseModel):
    task_key: str
    title: str
    language: str = ""
    workspace: dict[str, Any]
    instructions: str = ""
    instructions_file: str = ""
    params: dict[str, Any] = Field(default_factory=dict)


class TasksFile(BaseModel):
    tasks: list[TaskEntry]
