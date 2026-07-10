"""Capture: read a structured artifact the agent emitted into the workspace."""
from __future__ import annotations

from app.catalog.sdk import EvalContext, StageResult
from app.evaluation.render import render

MUTATES_WORKSPACE = False


def run(ctx: EvalContext, config: dict) -> StageResult:
    rel = render(config.get("path", ""), ctx.task)
    if not rel:
        return StageResult(name="file_artifact", ok=False, reason="missing_agent_response",
                           message="No artifact path configured.")
    path = ctx.workspace / rel
    if not path.is_file():
        return StageResult(name="file_artifact", ok=False, reason="missing_agent_response",
                           message=f"Expected artifact {rel} not found.")
    text = path.read_text(encoding="utf-8", errors="ignore")
    ctx.shared["artifact_text"] = text
    ok = bool(text.strip())
    return StageResult(name="file_artifact", ok=ok,
                       reason="" if ok else "missing_agent_response",
                       message="" if ok else "Artifact is empty.",
                       outputs={"bytes": len(text)})
