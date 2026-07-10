"""Capture: authoritative workspace delta. taskloop already computed the diff
and put it in ctx.diff_text; this stage records metrics/details."""
from __future__ import annotations

from app.catalog.sdk import EvalContext, StageResult

MUTATES_WORKSPACE = False


def run(ctx: EvalContext, config: dict) -> StageResult:
    lines = ctx.diff_text.count("\n")
    ctx.shared["diff_text"] = ctx.diff_text
    return StageResult(name="git_diff", ok=True, outputs={"diffLines": lines})
