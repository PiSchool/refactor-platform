"""Capture: surface token/model metrics parsed by the agent plugin."""
from __future__ import annotations

from app.catalog.sdk import EvalContext, StageResult

MUTATES_WORKSPACE = False


def run(ctx: EvalContext, config: dict) -> StageResult:
    s = ctx.session
    out = {
        "tokensInput": s.tokens_input if s else 0,
        "tokensOutput": s.tokens_output if s else 0,
        "model": s.model if s else "",
        "evalIterations": s.eval_iterations if s else 0,
    }
    return StageResult(name="events_metrics", ok=True, outputs=out)
