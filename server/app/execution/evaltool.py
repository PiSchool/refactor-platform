"""S1-eval in-session self-check. Writes an eval.sh into the workspace that
runs the benchmark's verify pipeline in advisory (leak-safe) mode, capped.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT = """#!/usr/bin/env bash
DIR="{workspace}"
MAX={max_attempts}
CF="$DIR/.eval_count"
N=$(cat "$CF" 2>/dev/null || echo 0); N=$((N+1)); echo "$N" > "$CF"
if [ "$N" -gt "$MAX" ]; then
  echo "FAILED"; echo "FAILED_STAGE: attempt_limit"
  echo "REASON: maximum self-check attempts ($MAX) reached."
  echo "FIX_GUIDANCE: stop retrying and finish."; exit 0
fi
{python} -m app.evaluation.check --run-task {run_task_id}
"""


def install(run_task_id: str, workspace: Path, max_attempts: int) -> Path:
    script = workspace / "eval.sh"
    script.write_text(_SCRIPT.format(
        workspace=str(workspace), max_attempts=max_attempts,
        python=sys.executable, run_task_id=run_task_id))
    script.chmod(0o755)
    return script
