"""Verify: the agent actually changed the workspace (non-empty diff)."""
from __future__ import annotations

from app.catalog.sdk import EvalContext, StageResult

MUTATES_WORKSPACE = False


def _summary(diff: str) -> str:
    files = diff.count("\ndiff --git ") + diff.startswith("diff --git ")
    adds = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    dels = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
    return f"{files} file{'' if files == 1 else 's'} changed, +{adds} −{dels}."


def run(ctx: EvalContext, config: dict) -> StageResult:
    if ctx.diff_text.strip():
        return StageResult(name="workspace_changed", ok=True, message=_summary(ctx.diff_text))
    return StageResult(name="workspace_changed", ok=False, reason="apply_failed",
                       message="No changes were made to the repository.")
