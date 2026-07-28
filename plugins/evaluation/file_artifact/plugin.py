"""Read the file a benchmark asked the agent to write.

A benchmark that wants a structured answer rather than an edit names the file in
its manifest; this reads it back and fails when it is absent or empty. The path
may depend on the task, so it is rendered over the task's fields.
"""
from __future__ import annotations

from app.catalog.sdk import (
    EvalContext,
    EvaluationPlugin,
    MetricOption,
    MetricSpec,
    StageResult,
    render,
)


class Plugin(EvaluationPlugin):
    key = "file_artifact"
    reason = "missing_agent_response"

    spec = MetricSpec(
        title="Agent response file",
        summary="Reads a file the agent was asked to write, and fails when it is missing or empty.",
        requires="a path declared by the benchmark",
        options=(
            MetricOption(
                key="path",
                label="File path",
                type="string",
                default="",
                help="Relative to the workspace. Task fields interpolate, e.g. {{ params.target }}.",
            ),
        ),
        outputs=("bytes",),
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        rel = render(config.get("path", ""), ctx.task)
        if not rel:
            return StageResult(ok=False, reason=self.reason,
                               message="No artifact path configured.")
        path = ctx.workspace / rel
        if not path.is_file():
            return StageResult(ok=False, reason=self.reason,
                               message=f"Expected artifact {rel} not found.")
        text = path.read_text(encoding="utf-8", errors="ignore")
        ctx.shared["artifact_text"] = text
        ok = bool(text.strip())
        return StageResult(ok=ok,
                           reason="" if ok else self.reason,
                           message="" if ok else "Artifact is empty.",
                           outputs={"bytes": len(text)})
