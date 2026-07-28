"""Record what the agent's session cost.

The numbers come from the agent adapter, which is the only component that can
read its own tool's event stream. This copies them onto the task's result so a
run's cost is in the export rather than only in a transcript.
"""
from __future__ import annotations

from app.catalog.sdk import EvalContext, EvaluationPlugin, MetricSpec, StageResult


class Plugin(EvaluationPlugin):
    key = "events_metrics"

    spec = MetricSpec(
        title="Agent session metrics",
        summary=("Records the token counts, model and evaluation-tool iterations the agent "
                 "adapter reported for this task."),
        requires="an agent session",
        gates=False,
        outputs=("tokensInput", "tokensOutput", "model", "evalIterations"),
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        session = ctx.session
        return StageResult(ok=True, outputs={
            "tokensInput": session.tokens_input if session else 0,
            "tokensOutput": session.tokens_output if session else 0,
            "model": session.model if session else "",
            "evalIterations": session.eval_iterations if session else 0,
        })
