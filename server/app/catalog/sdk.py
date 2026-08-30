"""Plugin SDK — the ONLY module plugins may import from the platform.

Benchmarks, agent tools, and LSP providers implement/consume these contracts.
Everything else in `app.*` is platform-internal.
"""
from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# Three things every metric would otherwise reimplement, so they are part of the
# surface rather than copied into each plugin: reading a test runner's counts,
# rendering a template over a task's fields, and running a command against a
# workspace under the platform's identity, process group and timeout rules.
from app.catalog.templating import render  # noqa: F401  (part of the plugin surface)
from app.catalog.reports import (  # noqa: F401
    counts,
    counts_message,
    is_compile_failure,
)
from app.catalog.workspace_commands import (  # noqa: F401
    CommandOutcome,
    run_in_workspace,
)

# The agent owns its workspace as an unprivileged user, while the platform and
# its evaluation stages read that workspace as root. Without this, every git
# read aborts with "dubious ownership".
GIT_SAFE_ENV = {"GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "safe.directory",
                "GIT_CONFIG_VALUE_0": "*"}


def git_read(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a read-only git command in a workspace, ownership check disabled."""
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True, env={**os.environ, **GIT_SAFE_ENV})


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
    # auth_wall | rate_limited | transport_error | model_mismatch | context_limit
    flags: set[str] = field(default_factory=set)
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
    #: Setup fidelity — did the agent actually exercise the mechanism its setup
    #: provides? A setup is a prompt plus a capability; a model may ignore both,
    #: and a harness that does not measure this cannot claim the setup was used.
    lsp_actions: int = 0
    subagent_invocations: int = 0
    eval_tool_invocations: int = 0
    retrieval_invocations: int = 0


@dataclass(frozen=True)
class SetupProfile:
    key: str                       # s1 | s1_lsp | s1_eval | s3
    name: str
    description: str
    lsp: bool = False
    eval_tool: bool = False
    subagents: bool = False
    retrieval: str = ""            # "" | "naive" | "ast" — S2 retrieval strategy
    prompt_block: str = ""
    archived_only: bool = False


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
    mcp_config: dict[str, Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    #: Left empty by a metric: the platform records the stage under the metric's
    #: own id, so the two can never disagree.
    name: str = ""
    ok: bool = True
    reason: str = ""
    message: str = ""
    log: str = ""
    outputs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricOption:
    """One option a metric accepts, declared rather than discovered by reading code.

    `type` drives the control the dashboard renders and the coercion it applies:

    * `string`, `integer`, `number`, `boolean` — a single scalar.
    * `choice` — one of `choices`.
    * `list` — several values; when `choices` is set, those are the allowed ones.
    * `reference` — a pointer into the task definition, such as `params.test_file`,
      for an option whose value differs per task.
    """
    key: str
    label: str
    type: str = "string"
    default: Any = None
    help: str = ""
    unit: str = ""
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class MetricSpec:
    """What a metric measures, what it needs, and how it can be configured.

    This is the metric's only self-description: the dashboard, the settings
    screen and the plugin check all read it, so a metric states each fact once.
    """
    title: str
    summary: str
    #: What must be present for the measurement to run at all, in one phrase
    #: ("a Java toolchain and Maven or Gradle", "the codebleu library"). Shown
    #: where the metric is listed, so an absent requirement is visible before a
    #: run rather than after it.
    requires: str = ""
    #: False for a metric that always reports success and only records numbers.
    #: A benchmark that lists such a metric among its gates is refused at load.
    gates: bool = True
    options: tuple[MetricOption, ...] = ()
    outputs: tuple[str, ...] = ()
    mutates_workspace: bool = False


@dataclass(frozen=True)
class PromptVariable:
    """One value the benchmark substitutes into a template.

    A required variable that an edit drops produces a prompt with a hole in it —
    a task with no code to refactor, for instance — so the platform refuses to
    save such an edit.
    """
    name: str
    summary: str
    required: bool = True


@dataclass(frozen=True)
class PromptSpec:
    """What a template is used for, how it is written, and what fills it in.

    `syntax` is `format` for `str.format_map` placeholders (`{name}`) or `jinja`
    for `{{ expression }}`. The two are not interchangeable: the wrong one
    reaches the agent as literal text.
    """
    applies_to: str = ""
    syntax: str = "jinja"
    variables: tuple[PromptVariable, ...] = ()


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

    def reference(self, spec: str) -> Any:
        """Resolve a metric option that points at task data instead of holding it.

        `params.test_file` reads the task's own field, `shared.rm_args` reads a
        value the benchmark published while preparing, and anything else is the
        literal. This is how one metric serves benchmarks whose fields differ.
        """
        if spec.startswith("params."):
            return self.task.params.get(spec[len("params."):])
        if spec.startswith("shared."):
            return self.shared.get(spec[len("shared."):])
        return spec

    def baseline_text(self, path: str) -> str | None:
        """The file's content as of the baseline commit, before the agent ran.

        Returns "" when the path did not exist in the baseline, so the agent
        created it, and None when git could not answer. None is not an empty
        baseline: a stage that cannot read the original must report that rather
        than compare the result against nothing.
        """
        listing = git_read(["ls-tree", "--name-only", "HEAD", "--", path], self.workspace)
        if listing.returncode != 0:
            return None
        if not listing.stdout.strip():
            return ""
        blob = git_read(["show", f"HEAD:{path}"], self.workspace)
        return blob.stdout if blob.returncode == 0 else None


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
    capabilities: dict[str, bool] = {"lsp": False, "subagents": False, "eval_tool": False, "retrieval": False}
    #: Paths the adapter writes inside the workspace (relative). The platform
    #: excludes them from the captured diff — they are scaffolding, not the
    #: agent's change.
    workspace_artifacts: tuple[str, ...] = ()

    @abstractmethod
    def prepare(self, session: SessionCtx) -> None: ...

    @abstractmethod
    def command(self, session: SessionCtx) -> CommandSpec: ...

    def resume_command(self, session: SessionCtx, prompt_path: Path) -> CommandSpec | None:
        """Resume the same logical agent session with a follow-up prompt.

        Setups may use this once for bounded protocol enforcement. Adapters
        whose CLI cannot resume return ``None`` and remain non-conformant when
        the model ignores a mandatory mechanism.
        """
        return None

    @abstractmethod
    def events_path(self, session: SessionCtx) -> Path | None: ...

    @abstractmethod
    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo: ...

    def cleanup(self, session: SessionCtx) -> None:
        return None


class BenchmarkPlugin:
    """Optional Python hooks for a benchmark. YAML-only benchmarks never
    subclass this — the loader uses this base with all-default behavior.

    A benchmark references metrics by id in its manifest and never defines one:
    a measurement lives in `plugins/evaluation/<id>/`, where every benchmark can
    reference it and an operator can retune it. The loader refuses a benchmark
    that tries.
    """

    key: str = ""

    def build_prompt(self, task: TaskDef, ctx: SessionCtx) -> str | None:
        return None

    def evaluate(self, ctx: EvalContext) -> EvalOutcome | None:
        return None

    def prepare(self, ctx: EvalContext) -> StageResult | None:
        """Put the workspace into the shape this benchmark's metrics expect.

        Runs once before the metrics, and publishes what they need through
        `ctx.shared`. It is not a measurement: it is recorded as the pipeline's
        preparation step, and a benchmark that implements it declares
        `evaluation.prepare` in its manifest and describes it below.
        """
        return None

    def describe_preparation(self) -> MetricSpec | None:
        """What `prepare` does, for the pipeline an operator reads before a run."""
        return None


class EvaluationPlugin:
    """One measurement, usable from any benchmark.

    A plugin provides exactly one metric and the metric's id is the plugin's
    directory name, so ids are unique by construction and a benchmark manifest
    names a directory an author can open.
    """

    key: str = ""

    #: What the metric measures, needs, records and accepts as options.
    spec: MetricSpec = MetricSpec(title="", summary="")

    #: The failure code recorded when this metric fails, one of the codes the
    #: results screen groups by. Empty for a metric that only records.
    reason: str = ""

    def measure(self, ctx: EvalContext, config: dict[str, Any]) -> StageResult:
        """Measure one finished task. `config` is the benchmark's option values."""
        raise NotImplementedError

    def availability(self) -> tuple[bool, str]:
        """Whether this deployment can run the measurement, and why not.

        Checked without a task, so an operator sees a missing tool or library on
        the Plugins screen instead of discovering it in a failed run.
        """
        return True, ""


class LSPPlugin(ABC):
    key: str = ""
    language: str = ""

    @abstractmethod
    def ensure(self) -> tuple[bool, str]: ...

    @abstractmethod
    def server_config(self, workspace: Path) -> dict[str, Any]: ...
