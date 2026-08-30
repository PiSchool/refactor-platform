"""A metric that belongs to nobody in particular.

Stands in for a third-party measurement: not shipped by the platform, not owned
by a benchmark, yet any benchmark can put it in its pipeline. Imports ONLY from
app.catalog.sdk.
"""
from __future__ import annotations

from app.catalog.sdk import (
    EvalContext,
    EvaluationPlugin,
    MetricOption,
    MetricSpec,
    StageResult,
)


class Plugin(EvaluationPlugin):
    key = "fixturemetric"
    reason = "diff_too_large"

    spec = MetricSpec(
        title="Change budget",
        summary="Fails a task whose diff touches more lines than the budget allows.",
        requires="nothing beyond the captured diff",
        options=(
            MetricOption(key="max_changed_lines", label="Budget", type="integer",
                         default=50, unit="lines"),
        ),
        outputs=("changedLines", "budget"),
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        budget = int(config.get("max_changed_lines", 50))
        changed = sum(
            1
            for line in ctx.diff_text.splitlines()
            if line[:1] in "+-" and not line.startswith(("+++", "---"))
        )
        return StageResult(
            ok=changed <= budget,
            reason="" if changed <= budget else self.reason,
            message=f"{changed} changed lines against a budget of {budget}",
            outputs={"changedLines": changed, "budget": budget},
        )
