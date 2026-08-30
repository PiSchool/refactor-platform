"""Read pass/fail counts out of a test runner's own output.

Several metrics run a test command and have to say what it found. "5/5 tests
passed" tells a reader what "Tests passed." does not, so the counts are parsed
from the runner's summary rather than inferred from the exit status.

Re-exported by `app.catalog.sdk`, which is the only module a plugin imports.
"""
from __future__ import annotations

import re

# unittest:  "Ran 5 tests in 0.01s" + "FAILED (failures=2, errors=1)"
_UNITTEST_RAN = re.compile(r"^Ran (\d+) tests?", re.M)
_UNITTEST_BAD = re.compile(r"(failures|errors)=(\d+)")
# pytest:    "===== 3 failed, 5 passed, 1 skipped in 0.5s ====="  /  "5 passed in 0.5s"
#
# Only ever read these counts off pytest's own summary line. Applied to a whole
# log the bare pattern also matches javac's "[INFO] 14 errors", and a compile
# failure is then reported as "0/14 tests passed".
_PYTEST_SUMMARY = re.compile(r"^(?:=+.*=+|\d+ \w+.*in \d+(?:\.\d+)?s.*)$", re.M)
_PYTEST = re.compile(r"(\d+) (passed|failed|error|errors|skipped|xfailed)")
# surefire:  "Tests run: 2032, Failures: 0, Errors: 3, Skipped: 15"
_SUREFIRE = re.compile(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+)(?:, Skipped: (\d+))?")
# javac gives no test summary at all — say so rather than inventing one.
_COMPILE_FAILURE = re.compile(r"Compilation failure|cannot find symbol|illegal start of")


def counts(log: str) -> tuple[int, int] | None:
    """(passed, total) from a test runner's summary, or None if not found."""
    if not log:
        return None

    # Maven Surefire — take the final, aggregate line
    sure = _SUREFIRE.findall(log)
    if sure:
        total, failures, errors, _skipped = sure[-1]
        total, failures, errors = int(total), int(failures), int(errors)
        return max(total - failures - errors, 0), total

    ran = _UNITTEST_RAN.findall(log)
    if ran:
        total = int(ran[-1])
        bad = sum(int(n) for _kind, n in _UNITTEST_BAD.findall(log))
        return max(total - bad, 0), total

    for line in _PYTEST_SUMMARY.findall(log):
        py = _PYTEST.findall(line)
        if not py:
            continue
        by: dict[str, int] = {}
        for n, kind in py:
            by[kind] = by.get(kind, 0) + int(n)
        passed = by.get("passed", 0)
        total = passed + by.get("failed", 0) + by.get("error", 0) + by.get("errors", 0)
        if total:
            return passed, total
    return None


def is_compile_failure(log: str) -> bool:
    """javac died before any test ran, so there is no test summary to report."""
    return bool(_COMPILE_FAILURE.search(log or ""))


def counts_message(log: str, ok: bool, noun: str = "tests") -> str:
    """One sentence stating what the runner reported."""
    parsed = counts(log)
    if parsed is None:
        if not ok and is_compile_failure(log):
            return "Compilation failed; no tests ran."
        return f"{noun.capitalize()} passed." if ok else f"{noun.capitalize()} failed."
    passed, total = parsed
    return f"{passed}/{total} {noun} passed."
