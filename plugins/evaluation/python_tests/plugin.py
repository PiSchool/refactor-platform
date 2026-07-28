"""Run one Python test file that ships with a benchmark's data.

The test lives outside the repository the agent edited, so it cannot be weakened
by the agent. It is executed against the modified workspace, with the repository
on `sys.path` when the test imports the package from a source checkout.

For the repository's own suite instead, see the `pytest_suite` metric.
"""
from __future__ import annotations

import sys

from app.catalog.sdk import (
    EvalContext,
    EvaluationPlugin,
    MetricOption,
    MetricSpec,
    StageResult,
    counts,
    counts_message,
    run_in_workspace,
)

# Tests written for 3.9 use ast aliases removed in 3.12. Restoring them is what
# lets the study's own test files run unmodified on a current interpreter.
_AST_SHIM = """\
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
import ast
if not hasattr(ast, 'Str'): ast.Str = ast.Constant
if not hasattr(ast, 'Bytes'): ast.Bytes = ast.Constant
if not hasattr(ast, 'Num'): ast.Num = ast.Constant
if not hasattr(ast, 'NameConstant'): ast.NameConstant = ast.Constant
"""


class Plugin(EvaluationPlugin):
    key = "python_tests"
    reason = "test_failed"

    spec = MetricSpec(
        title="Python test file",
        summary=("Runs one test file that ships with the benchmark data against the modified "
                 "workspace. Fails when the suite does."),
        requires="a test file in the benchmark's data directory",
        options=(
            MetricOption(key="test_from", label="Test file", type="reference", default="",
                         help="Where the path comes from, e.g. params.test_file. Resolved under the "
                              "benchmark's data directory."),
            MetricOption(key="cwd_hint_from", label="Working directory", type="reference", default="",
                         help="Optional task field naming a subdirectory to run from; ignored when it "
                              "does not exist in the workspace."),
            MetricOption(key="sys_path_repo_root", label="Put the repository on sys.path",
                         type="boolean", default=True,
                         help="Needed when the test imports the package from a source checkout."),
            MetricOption(key="compat_shim", label="Compatibility shim", type="choice", default="",
                         choices=("", "py39_ast"),
                         help="py39_ast restores the ast aliases removed in 3.12 so tests written "
                              "for 3.9 still run."),
            MetricOption(key="timeout", label="Timeout", type="integer", default=300, unit="seconds"),
        ),
        outputs=("testsPassed", "testsTotal"),
        mutates_workspace=True,
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        test_rel = ctx.reference(config.get("test_from", ""))
        if not test_rel:
            return StageResult(ok=False, reason=self.reason, message="No test file configured.")
        test_abs = (ctx.data_root / test_rel).resolve()
        if not test_abs.is_file():
            return StageResult(ok=False, reason=self.reason,
                               message=f"Test file not found: {test_rel}")

        cwd = ctx.workspace
        hint_ref = config.get("cwd_hint_from")
        if hint_ref:
            hint = ctx.reference(hint_ref)
            if hint and (ctx.workspace / hint).is_dir():
                cwd = ctx.workspace / hint

        header = ""
        if config.get("sys_path_repo_root", True):
            header += f"import sys; sys.path.insert(0, {str(ctx.workspace)!r})\n"
        if config.get("compat_shim") == "py39_ast":
            header += _AST_SHIM
        runner = cwd / "_rp_test_runner.py"
        runner.write_text(
            header + f'\nimport runpy; runpy.run_path({str(test_abs)!r}, run_name="__main__")\n',
            encoding="utf-8",
        )
        try:
            outcome = run_in_workspace(
                cwd,
                [sys.executable, "-W", "ignore::DeprecationWarning", str(runner)],
                timeout=int(config.get("timeout", 300)),
                demote=False,
            )
        finally:
            runner.unlink(missing_ok=True)

        log = outcome.output.strip()
        if outcome.timed_out:
            log = f"test timed out after {config.get('timeout', 300)}s\n{log}"
        parsed = counts(log)
        return StageResult(
            ok=outcome.ok,
            reason="" if outcome.ok else self.reason,
            message=counts_message(log, outcome.ok),
            log=log,
            outputs={"testsPassed": parsed[0], "testsTotal": parsed[1]} if parsed else {},
        )
