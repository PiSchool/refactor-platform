"""plugin.yaml / tasks.yaml schemas (Pydantic-validated at discovery)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.execution.setups import SETUPS

# Single source of truth: the platform-defined setups. Kept in sync with
# execution/setups.py so adding a setup there can never silently drop a
# benchmark that declares it (which is exactly what a hardcoded list did).
SETUP_KEYS = tuple(SETUPS)


class FacetSpec(BaseModel):
    key: str
    label: str


class PromptVariableSpec(BaseModel):
    """One value the benchmark substitutes into its template.

    Declaring these is what lets the dashboard mark a template that has dropped
    a value the benchmark relies on, and refuse to save it. Without a
    declaration the platform can only report that the template exists.
    """
    name: str
    summary: str = ""
    required: bool = True


class PromptSpec(BaseModel):
    template: str  # path relative to plugin dir, Jinja2 over {task, params}
    #: Which tasks select this template. A benchmark with one template says so.
    appliesTo: str = "every task in this benchmark"
    variables: list[PromptVariableSpec] = Field(default_factory=list)
    #: The task field naming the directory this benchmark's own instructions
    #: write their paths relative to, when that is not the repository root
    #: (`params.cwd_hint`). The platform states the difference in the prompt
    #: rather than leaving the agent to discover it: RefactorBench asks for
    #: `requests/utils.py` in a checkout that keeps it at `src/requests/utils.py`.
    pathsRelativeTo: str = ""


class DataSpec(BaseModel):
    bootstrap: str = "data_bootstrap.py"
    # Bump when bootstrap's definition of a complete installation changes.
    # The value is persisted in .ready so stale volumes repair on startup.
    revision: str = "ok"


class Stage(BaseModel):
    """One metric in a pipeline, with the options it runs with.

    Written either as a bare id (`git_diff`) or as `{preset: id, config: {...}}`.
    """
    preset: str
    config: dict[str, Any] = Field(default_factory=dict)


class ArtifactCapture(BaseModel):
    path: str                       # workspace-relative, Jinja2 over {task, params}
    seed: bool = False
    template: str = ""              # inline template text seeded at workspace prep


class EvaluationSpec(BaseModel):
    #: The benchmark's own preparation step, named as it is recorded. Declaring
    #: it requires the Python hook to implement `prepare` and describe it; a
    #: mismatch either way fails the load. It measures nothing and gates nothing:
    #: it puts the workspace into the shape the metrics below expect.
    prepare: str = ""
    #: Metrics that record numbers and evidence, in order.
    capture: list[Stage] = Field(default_factory=list)
    artifact: ArtifactCapture | None = None            # required when capture includes file_artifact
    #: Metrics that can fail, in order.
    verify: list[Stage] = Field(default_factory=list)
    #: Boolean expression over the verify stage ids.
    passed: str = ""

    @field_validator("capture", "verify", mode="before")
    @classmethod
    def _accept_bare_ids(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        return [{"preset": item} if isinstance(item, str) else item for item in value]

    @model_validator(mode="after")
    def _artifact_path_reaches_its_metric(self) -> "EvaluationSpec":
        """The declared artifact is what `file_artifact` reads.

        Stated here so the scoring engine needs no branch on a metric's name: it
        runs every stage with the options the manifest gives it.
        """
        if self.artifact is None:
            return self
        for stage in (*self.capture, *self.verify):
            if stage.preset == "file_artifact" and "path" not in stage.config:
                stage.config["path"] = self.artifact.path
        return self

    @property
    def capture_ids(self) -> list[str]:
        return [stage.preset for stage in self.capture]

    @property
    def verify_ids(self) -> list[str]:
        return [stage.preset for stage in self.verify]


class DisplaySpec(BaseModel):
    tabs: dict[str, str] = Field(default_factory=dict)


class BenchmarkManifest(BaseModel):
    type: Literal["benchmark"]
    key: str
    name: str
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
    entrypoint: str = "plugin:Plugin"
    # Executable the adapter drives. Declared here so the platform can report an
    # uninstalled CLI before a run starts instead of failing inside the PTY.
    binary: str = ""
    install: str = ""            # one-line hint shown when `binary` is absent
    capabilities: dict[str, bool] = Field(default_factory=dict)


class EvaluationManifest(BaseModel):
    type: Literal["evaluation"]
    #: The metric's id, which is also the plugin's directory name.
    key: str
    name: str = ""
    entrypoint: str = "plugin:Plugin"
    #: Shown when the metric reports it cannot run here, e.g. "pip install codebleu".
    install: str = ""


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
