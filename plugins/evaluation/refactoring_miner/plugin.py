"""Ask RefactoringMiner whether the declared refactoring is present.

The detector compares the file as it was against the file as the agent left it
and answers with the refactorings it recognises. The comparison inputs differ per
benchmark, so the benchmark stages them while preparing and this reads them from
the value it publishes.

Its verdict is the study's own definition of a correct refactoring, which is why
it gates rather than records.
"""
from __future__ import annotations

import subprocess

from app.catalog.sdk import (
    EvalContext,
    EvaluationPlugin,
    MetricOption,
    MetricSpec,
    StageResult,
)


class Plugin(EvaluationPlugin):
    key = "refactoring_miner"
    reason = "ast_verification_failed"

    spec = MetricSpec(
        title="RefactoringMiner detection",
        summary=("Asks RefactoringMiner whether the declared refactoring is present between the "
                 "baseline and the agent's version of the file."),
        requires="the RefactoringMiner distribution in the benchmark's data directory",
        options=(
            MetricOption(key="binary_from_data", label="Detector path", type="string", default="",
                         help="Relative to the benchmark's data directory."),
            MetricOption(key="args_from", label="Detector arguments", type="reference",
                         default="shared.rm_args",
                         help="Where the before/after pair comes from. The benchmark publishes it "
                              "while preparing the workspace."),
        ),
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        rel = config.get("binary_from_data", "")
        binary = ctx.data_root / rel
        if not binary.is_file():
            return StageResult(ok=False, reason=self.reason,
                               message=f"RefactoringMiner binary missing: {rel}")
        args = ctx.reference(config.get("args_from", "shared.rm_args"))
        if not args:
            return StageResult(ok=False, reason=self.reason,
                               message="No RefactoringMiner inputs prepared.")

        proc = subprocess.run([str(binary), *args], capture_output=True, text=True)
        if proc.returncode != 0:
            return StageResult(ok=False, reason=self.reason,
                               message="RefactoringMiner execution failed.",
                               log=(proc.stdout + proc.stderr)[-8000:])
        lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
        ok = bool(lines) and lines[-1].split()[0].lower() == "true"
        return StageResult(
            ok=ok,
            reason="" if ok else self.reason,
            message="Refactoring detected." if ok else "Declared refactoring not detected.",
            log=proc.stdout[-8000:],
        )
