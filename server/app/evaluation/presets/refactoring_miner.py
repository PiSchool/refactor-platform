"""Verify: run the external RefactoringMiner detector (shipped in plugin data).

Inputs and mode are published to ctx.shared by a benchmark stage (swe):
  shared["rm_args"]: list[str] passed after the binary path.
ok = the detector's last stdout line starts with "true".
"""
from __future__ import annotations

import subprocess

from app.catalog.sdk import EvalContext, StageResult

MUTATES_WORKSPACE = False


def run(ctx: EvalContext, config: dict) -> StageResult:
    rel = config.get("binary_from_data", "")
    binary = ctx.data_root / rel
    if not binary.is_file():
        return StageResult(name="refactoring_miner", ok=False, reason="ast_verification_failed",
                           message=f"RefactoringMiner binary missing: {rel}")
    args = ctx.shared.get("rm_args")
    if not args:
        return StageResult(name="refactoring_miner", ok=False, reason="ast_verification_failed",
                           message="No RefactoringMiner inputs prepared.")
    proc = subprocess.run([str(binary), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        return StageResult(name="refactoring_miner", ok=False, reason="ast_verification_failed",
                           message="RefactoringMiner execution failed.",
                           log=(proc.stdout + proc.stderr)[-8000:])
    lines = [l for l in proc.stdout.strip().splitlines() if l.strip()]
    ok = bool(lines) and lines[-1].split()[0].lower() == "true"
    return StageResult(name="refactoring_miner", ok=ok,
                       reason="" if ok else "ast_verification_failed",
                       message="Refactoring detected." if ok else "Declared refactoring not detected.",
                       log=proc.stdout[-8000:])