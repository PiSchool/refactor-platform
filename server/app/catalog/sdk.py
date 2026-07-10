"""Plugin SDK — the ONLY module plugins may import from the platform.

Benchmarks, agent tools, and LSP providers implement/consume these contracts.
Everything else in `app.*` is platform-internal.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class WorkspaceSpec:
    type: str                      # "git" | "snapshot"
    source: str                    # git: repo URL; snapshot: path relative to plugin data dir
    ref: str | None = None         # git: pinned commit sha


@dataclass(frozen=True)
class TaskDef:
    task_key: str
    title: str
    language: str
    workspace: WorkspaceSpec
    instructions: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandSpec:
    argv: list[str]
    env: dict[str, str]
    cwd: Path


@dataclass
class SessionInfo:
    tokens_input: int = 0
    tokens_output: int = 0
    model: str = ""
    response_text: str = ""
    flags: set[str] = field(default_factory=set)   # auth_wall | rate_limited | transport_error | model_mismatch
    eval_iterations: int = 0
    readable_transcript: str = ""
    #: subset of tokens_input served from the provider's prompt cache (billed lower)
    tokens_cache_read: int = 0
    #: subset of tokens_output spent on reasoning
    tokens_reasoning: int = 0
    #: context occupancy at the end of the session, in tokens
    context_tokens: int = 0
    #: how often the agent compacted its context to keep going
    compaction_count: int = 0
    #: how often the provider rejected a request for exceeding the context window
    context_overflow_count: int = 0


@dataclass(frozen=True)
class SetupProfile:
    key: str                       # s1 | s1_lsp | s1_eval | s3
    name: str
    description: str
    lsp: bool = False
    eval_tool: bool = False
    subagents: bool = False
    prompt_block: str = ""


@dataclass
class SessionCtx:
    run_id: str
    run_task_id: str
    session_id: str
    task: TaskDef
    workspace: Path
    artifacts_dir: Path
    prompt_path: Path
    config_dir: Path               # agent-private per-session root (used as HOME override)
    model: str
    setup: SetupProfile
    requested_env: dict[str, str]
    lsp_config: dict[str, Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    name: str
    ok: bool
    reason: str = ""
    message: str = ""
    log: str = ""
    outputs: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalContext:
    task: TaskDef
    workspace: Path
    artifacts_dir: Path
    data_root: Path
    session: SessionInfo | None
    diff_text: str
    advisory: bool
    shared: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalOutcome:
    passed: bool
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    stages: list[StageResult] = field(default_factory=list)


StageFn = Callable[[EvalContext, dict[str, Any]], StageResult]


class AgentPlugin(ABC):
    """Adapter for one AI CLI tool. The platform owns the process lifecycle;
    the plugin only declares how to invoke and interpret the tool."""

    key: str = ""
    capabilities: dict[str, bool] = {"lsp": False, "subagents": False, "eval_tool": False}
    models: list[str] = []
    #: Paths the adapter writes inside the workspace (relative). The platform
    #: excludes them from the captured diff — they are scaffolding, not the
    #: agent's change.
    workspace_artifacts: tuple[str, ...] = ()

    @abstractmethod
    def prepare(self, session: SessionCtx) -> None: ...

    @abstractmethod
    def command(self, session: SessionCtx) -> CommandSpec: ...

    @abstractmethod
    def events_path(self, session: SessionCtx) -> Path | None: ...

    @abstractmethod
    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo: ...

    def cleanup(self, session: SessionCtx) -> None:
        return None


class BenchmarkPlugin:
    """Optional Python hooks for a benchmark. YAML-only benchmarks never
    subclass this — the loader uses this base with all-default behavior."""

    key: str = ""

    def build_prompt(self, task: TaskDef, ctx: SessionCtx) -> str | None:
        return None

    def evaluate(self, ctx: EvalContext) -> EvalOutcome | None:
        return None

    def stages(self) -> dict[str, StageFn]:
        return {}


class LSPPlugin(ABC):
    key: str = ""
    language: str = ""

    @abstractmethod
    def ensure(self) -> tuple[bool, str]: ...

    @abstractmethod
    def server_config(self, workspace: Path) -> dict[str, Any]: ...
