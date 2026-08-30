"""One measurement, usable from any benchmark's pipeline.

A metric answers: did this task's result satisfy something checkable, and what
did the check see. It returns a `StageResult`; the platform records it under this
plugin's id and decides the verdict from the benchmark's rule over its gates.

`spec` is what puts the metric on equal footing with a shipped one: a title, a
summary, what it needs, whether it can fail a task, what it records, and typed
options with defaults — instead of an identifier an operator has to look up.

Imports only from `app.catalog.sdk`.
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
    #: The metric's id, which is this directory's name. A benchmark references
    #: `example_metric` in its manifest; renaming the directory renames the metric.
    key = "example_metric"

    #: Recorded when this metric fails, so failures group with each other.
    reason = "too_few_lines_changed"

    spec = MetricSpec(
        title="Lines added",
        summary="Counts added lines in the captured diff and compares them against a minimum.",
        requires="nothing beyond the captured diff",
        outputs=("addedLines",),
        options=(
            MetricOption(
                key="minimum",
                label="Minimum added lines",
                type="integer",
                default=1,
                help="Fewer added lines than this fails the stage.",
            ),
        ),
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        minimum = int(config.get("minimum", 1))
        added = sum(
            1 for line in ctx.diff_text.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        ok = added >= minimum
        return StageResult(
            ok=ok,
            reason="" if ok else self.reason,
            message=f"{added} line(s) added, {minimum} required",
            outputs={"addedLines": added},
        )

    def availability(self) -> tuple[bool, str]:
        """Whether this deployment can run the measurement at all.

        Checked without a task, so a missing tool or library is visible on the
        Plugins screen instead of inside a failed run. This one needs nothing.
        """
        return True, ""
