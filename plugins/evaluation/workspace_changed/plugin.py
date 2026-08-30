"""Did the agent change the repository at all.

The cheapest gate there is, and the one that separates "the refactoring is
wrong" from "nothing was applied". Every benchmark uses it.
"""
from __future__ import annotations

from app.catalog.sdk import EvalContext, EvaluationPlugin, MetricSpec, StageResult


class Plugin(EvaluationPlugin):
    key = "workspace_changed"
    reason = "apply_failed"

    spec = MetricSpec(
        title="Workspace changed",
        summary="Fails when the agent left the repository byte-for-byte unchanged.",
        requires="nothing beyond the captured diff",
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        if ctx.diff_text.strip():
            return StageResult(ok=True, message=_summary(ctx.diff_text))
        return StageResult(ok=False, reason=self.reason,
                           message="No changes were made to the repository.")


def _summary(diff: str) -> str:
    files = diff.count("\ndiff --git ") + diff.startswith("diff --git ")
    adds = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    dels = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
    return f"{files} file{'' if files == 1 else 's'} changed, +{adds} −{dels}."
