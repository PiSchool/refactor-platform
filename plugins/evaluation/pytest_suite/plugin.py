"""Run the test suite that lives in the repository under test.

This is what makes a Python refactoring verdict honest: a change that performs
the requested transformation but breaks behaviour fails here.

For a single test file shipped with a benchmark's data instead, see the
`python_tests` metric.
"""
from __future__ import annotations

import re
import shutil
import sys

from app.catalog.sdk import (
    EvalContext,
    EvaluationPlugin,
    MetricOption,
    MetricSpec,
    StageResult,
    run_in_workspace,
)

SUMMARY = re.compile(r"(?P<count>\d+) (?P<state>passed|failed|error|errors|skipped|xfailed)")


class Plugin(EvaluationPlugin):
    key = "pytest_suite"
    reason = "test_failed"

    spec = MetricSpec(
        title="Repository test suite",
        summary=("Runs the tests that live in the repository under test, so a refactoring that "
                 "changes behaviour fails even when it is the refactoring that was asked for."),
        requires="pytest in the runtime environment",
        options=(
            MetricOption(key="targets", label="Targets", type="list", default=[],
                         help="Paths passed to pytest, relative to the workspace. Empty runs the "
                              "whole repository."),
            MetricOption(key="targets_from", label="Targets from the task", type="reference",
                         default="",
                         help="params.<key> holding those paths, used when Targets is unset."),
            MetricOption(key="timeout", label="Timeout", type="integer", default=900, unit="seconds"),
            MetricOption(key="maxfail", label="Stop after failures", type="integer", default=1,
                         help="1 abandons the suite at the first failure, which is enough for a "
                              "verdict."),
            MetricOption(key="extra_args", label="Extra pytest arguments", type="list", default=[]),
        ),
        outputs=("passed", "failed", "skipped", "status", "targets"),
        mutates_workspace=True,
    )

    def availability(self) -> tuple[bool, str]:
        if shutil.which("pytest") or _importable("pytest"):
            return True, ""
        return False, "pytest is not installed in the runtime environment"

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        targets = _targets(ctx, config)
        argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                f"--maxfail={int(config.get('maxfail', 1))}"]
        argv += [str(a) for a in config.get("extra_args", [])]
        argv += targets
        timeout = int(config.get("timeout", 900))

        outcome = run_in_workspace(
            ctx.workspace, argv, timeout=timeout, demote=False,
            # The suite runs after the diff is captured; caches and bytecode would
            # still appear in the workspace an operator inspects afterwards.
            env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"},
        )
        output = outcome.output.strip()
        if outcome.timed_out:
            output, status = f"suite timed out after {timeout}s\n{output}", "timeout"
        elif outcome.returncode is None:
            return StageResult(ok=False, reason=self.reason,
                               message="pytest is not installed in the runtime environment.")
        else:
            status = f"exit {outcome.returncode}"

        counts = _counts(output)
        passed = counts.get("passed", 0)
        failed = counts.get("failed", 0) + counts.get("error", 0)
        if counts:
            total = passed + failed
            message = f"{passed}/{total} tests passed." if total else f"Suite finished ({status})."
        else:
            message = f"Suite produced no test summary ({status})."
        return StageResult(
            ok=outcome.ok, reason="" if outcome.ok else self.reason, message=message,
            log=output[-16000:],
            outputs={"passed": passed, "failed": failed, "skipped": counts.get("skipped", 0),
                     "status": status, "targets": targets},
        )


def _counts(output: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in SUMMARY.finditer(output[-4000:]):
        state = match.group("state").rstrip("s")
        counts[state] = counts.get(state, 0) + int(match.group("count"))
    return counts


def _targets(ctx: EvalContext, config: dict) -> list[str]:
    raw = config.get("targets")
    if raw is None:
        raw = ctx.reference(str(config.get("targets_from", "") or ""))
    if not raw:
        return []
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    return [str(part).strip() for part in raw if str(part).strip()]


def _importable(module: str) -> bool:
    from importlib.util import find_spec

    try:
        return find_spec(module) is not None
    except (ImportError, ValueError):
        return False
