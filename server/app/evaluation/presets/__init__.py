"""Core evaluation presets. Each exposes run(ctx, config) -> StageResult and
an optional MUTATES_WORKSPACE flag (advisory mode copies the workspace when
any verify stage mutates it).
"""
from __future__ import annotations

from app.evaluation.presets import (
    events_metrics,
    file_artifact,
    git_diff,
    java_build,
    python_tests,
    refactoring_miner,
    workspace_changed,
)

CORE_PRESETS = {
    "git_diff": git_diff,
    "events_metrics": events_metrics,
    "file_artifact": file_artifact,
    "workspace_changed": workspace_changed,
    "python_tests": python_tests,
    "java_build": java_build,
    "refactoring_miner": refactoring_miner,
}

# reason codes surfaced when a verify stage fails
REASON_BY_STAGE = {
    "workspace_changed": "apply_failed",
    "python_tests": "test_failed",
    "java_build": "compile_test_failed",
    "refactoring_miner": "ast_verification_failed",
    "file_artifact": "missing_agent_response",
}
