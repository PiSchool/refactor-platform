"""Verify: run the task's Python test file against the modified workspace.

The test file lives in the plugin data dir (outside the repo), referenced via
a params field. Supports the Py3.9 AST-compat shim so older RefactorBench
tests run on 3.12.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.catalog.sdk import EvalContext, StageResult
from app.evaluation.presets._util import counts_message, resolve, test_counts

MUTATES_WORKSPACE = True

_AST_SHIM = """\
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
import ast
if not hasattr(ast, 'Str'): ast.Str = ast.Constant
if not hasattr(ast, 'Bytes'): ast.Bytes = ast.Constant
if not hasattr(ast, 'Num'): ast.Num = ast.Constant
if not hasattr(ast, 'NameConstant'): ast.NameConstant = ast.Constant
"""


def run(ctx: EvalContext, config: dict) -> StageResult:
    test_rel = resolve(ctx, config.get("test_from", ""))
    if not test_rel:
        return StageResult(name="python_tests", ok=False, reason="test_failed",
                           message="No test file configured.")
    test_abs = (ctx.data_root / test_rel).resolve()
    if not test_abs.is_file():
        return StageResult(name="python_tests", ok=False, reason="test_failed",
                           message=f"Test file not found: {test_rel}")

    cwd = ctx.workspace
    hint_ref = config.get("cwd_hint_from")
    if hint_ref:
        hint = resolve(ctx, hint_ref)
        if hint and (ctx.workspace / hint).is_dir():
            cwd = ctx.workspace / hint

    shim = cwd / "_rp_test_runner.py"
    header = ""
    if config.get("sys_path_repo_root", True):
        header += f"import sys; sys.path.insert(0, {str(ctx.workspace)!r})\n"
    if config.get("compat_shim") == "py39_ast":
        header += _AST_SHIM
    shim.write_text(
        header + f'\nimport runpy; runpy.run_path({str(test_abs)!r}, run_name="__main__")\n',
        encoding="utf-8",
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-W", "ignore::DeprecationWarning", str(shim)],
            cwd=str(cwd), capture_output=True, text=True,
            timeout=int(config.get("timeout", 300)),
        )
        ok = proc.returncode == 0
        log = (proc.stdout + "\n" + proc.stderr).strip()
    except subprocess.TimeoutExpired as exc:
        ok, log = False, f"test timed out: {exc}"
    finally:
        shim.unlink(missing_ok=True)

    counts = test_counts(log)
    return StageResult(name="python_tests", ok=ok,
                       reason="" if ok else "test_failed",
                       message=counts_message(log, ok),
                       log=log,
                       outputs={"testsPassed": counts[0], "testsTotal": counts[1]} if counts else {})
