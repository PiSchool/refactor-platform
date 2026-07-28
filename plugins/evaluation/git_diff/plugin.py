"""Record the diff the agent produced.

The platform computes the diff before scoring; this records it as the run's
evidence and publishes it for any metric that reads the change itself.
"""
from __future__ import annotations

from app.catalog.sdk import EvalContext, EvaluationPlugin, MetricSpec, StageResult


class Plugin(EvaluationPlugin):
    key = "git_diff"

    spec = MetricSpec(
        title="Workspace diff",
        summary="Records the unified diff of everything the agent changed, and how many lines it spans.",
        requires="nothing beyond the captured diff",
        gates=False,
        outputs=("diffLines",),
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        ctx.shared["diff_text"] = ctx.diff_text
        return StageResult(ok=True, outputs={"diffLines": ctx.diff_text.count("\n")})
