"""Fail-closed build preflight for untouched Java task workspaces."""
from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.catalog.sdk import EvalContext, StageResult
from app.evaluation import registry


@dataclass(frozen=True)
class BaselineResult:
    ok: bool
    reason: str
    message: str
    timeout_seconds: int

    def details(self) -> dict:
        return {
            "ok": self.ok,
            "reason": self.reason,
            "message": self.message,
            "timeoutSeconds": self.timeout_seconds,
        }


class BaselineRejected(RuntimeError):
    def __init__(self, result: BaselineResult):
        super().__init__(result.message)
        self.result = result


def _java_build_config(loaded_benchmark) -> dict | None:
    for stage in loaded_benchmark.manifest.evaluation.verify:
        if stage.preset == "java_build":
            return dict(stage.config)
    return None


def _write_log(artifacts: Path, result: StageResult) -> None:
    eval_dir = artifacts / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    text = result.log or result.message
    (eval_dir / "baseline_java_build.log").write_text(text, encoding="utf-8")


def run_java_baseline(
    loaded_benchmark,
    task,
    workspace: Path,
    artifacts: Path,
    *,
    timeout_seconds: int,
) -> BaselineResult | None:
    """Build/test an exact disposable copy before the agent sees the task."""
    if task.language.lower() != "java":
        return None
    config = _java_build_config(loaded_benchmark)
    if config is None:
        return None
    # The benchmark gates on a build, so a deployment without that metric cannot
    # establish a baseline and must not proceed as though it had.
    metric = registry.get("java_build")
    if metric is None:
        return BaselineResult(
            ok=False,
            reason="baseline_infrastructure_error",
            message="The java_build metric is not installed, so no baseline can be established.",
            timeout_seconds=max(1, int(timeout_seconds)),
        )

    timeout_seconds = max(1, int(timeout_seconds))
    config["timeout_seconds"] = timeout_seconds
    artifacts.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix=".java-baseline-", dir=artifacts))
    baseline_workspace = temporary_root / "workspace"
    stage_result: StageResult
    cleanup_error = ""
    try:
        shutil.copytree(workspace, baseline_workspace, symlinks=True)
        context = EvalContext(
            task=task,
            workspace=baseline_workspace,
            artifacts_dir=artifacts,
            data_root=loaded_benchmark.data_dir,
            session=None,
            diff_text="",
            advisory=True,
        )
        try:
            stage_result = metric.measure(context, config)
        except Exception as exc:
            stage_result = StageResult(
                name="java_build",
                ok=False,
                reason="baseline_infrastructure_error",
                message="Java baseline infrastructure failed.",
                log=f"{type(exc).__name__}: {exc}\n",
            )
    except Exception as exc:
        stage_result = StageResult(
            name="java_build",
            ok=False,
            reason="baseline_infrastructure_error",
            message="Java baseline workspace preparation failed.",
            log=f"{type(exc).__name__}: {exc}\n",
        )
    finally:
        try:
            shutil.rmtree(temporary_root)
        except OSError as exc:
            cleanup_error = f"{type(exc).__name__}: {exc}"

    if cleanup_error:
        stage_result = StageResult(
            name="java_build",
            ok=False,
            reason="baseline_cleanup_failed",
            message="Java baseline workspace cleanup failed.",
            log=f"{stage_result.log.rstrip()}\n{cleanup_error}\n",
        )
    _write_log(artifacts, stage_result)
    return BaselineResult(
        ok=stage_result.ok,
        reason=stage_result.reason,
        message=stage_result.message,
        timeout_seconds=timeout_seconds,
    )