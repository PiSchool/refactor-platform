"""Did the Python change perform the refactoring that was asked for?

Compares the baseline and modified parse trees and names what changed, so a
Python benchmark has the same kind of verdict RefactoringMiner gives for Java.

With no expectation configured it passes when any refactoring is detected.
"""
from __future__ import annotations

import re

from app.catalog.sdk import (
    EvalContext,
    EvaluationPlugin,
    MetricOption,
    MetricSpec,
    StageResult,
)

# A plugin's own modules are imported relative to it, so a second metric
# plugin shipping its own `detect.py` cannot answer for this one.
from . import detect as detector

DIFF_TARGET = re.compile(r"^\+\+\+ b/(?P<path>.+)$", re.M)
DIFF_SOURCE = re.compile(r"^--- a/(?P<path>.+)$", re.M)
MAX_FILES = 200


class Plugin(EvaluationPlugin):
    key = "pyrefactor"
    reason = "ast_verification_failed"

    spec = MetricSpec(
        title="Python refactoring detected",
        summary=("Compares the baseline and modified parse trees and names the refactoring that was "
                 "performed. Fails when it is not the one asked for, or when the file no longer parses."),
        requires="nothing beyond the workspace and its git baseline",
        options=(
            MetricOption(key="expected", label="Expected refactorings", type="list", default=[],
                         choices=tuple(detector.KINDS),
                         help="One or more kinds. Empty accepts any refactoring the detector finds."),
            MetricOption(key="expected_from", label="Expected from the task", type="reference",
                         default="",
                         help="params.<key> holding those kinds, used when Expected is unset."),
            MetricOption(key="files", label="Files", type="list", default=[],
                         help="Paths to inspect instead of every Python file in the diff."),
        ),
        outputs=("detected", "detectedCount", "expected", "matched", "filesAnalysed", "parseErrors"),
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        paths = [str(p) for p in config.get("files", [])] or _changed_python_files(ctx.diff_text)
        if not paths:
            return StageResult(ok=False, reason=self.reason,
                               message="No Python file was changed.")

        # An unreadable baseline is reported, never treated as an empty one: with
        # nothing to compare against, every refactoring looks like a new file and
        # a correct change would be scored as no refactoring at all.
        before: dict[str, str] = {}
        for path in paths:
            original = ctx.baseline_text(path)
            if original is None:
                return StageResult(
                    ok=False, reason=self.reason,
                    message=f"Could not read {path} as it was before the agent ran.")
            before[path] = original

        after: dict[str, str] = {}
        for path in paths:
            candidate = ctx.workspace / path
            after[path] = (candidate.read_text(encoding="utf-8", errors="replace")
                           if candidate.is_file() else "")

        findings = detector.detect(before, after)
        broken = [f for f in findings if f.kind == detector.SYNTAX_ERROR]
        refactorings = [f for f in findings if f.kind != detector.SYNTAX_ERROR]
        expected = _expected(ctx, config)
        matched = detector.matches(refactorings, expected)

        if broken:
            message = f"Modified Python does not parse: {broken[0].detail}"
            ok = False
        elif expected:
            ok = bool(matched)
            message = (f"Detected {', '.join(matched)}." if ok
                       else f"Expected {', '.join(expected)}; detected "
                            f"{', '.join(sorted({f.kind for f in refactorings})) or 'nothing'}.")
        else:
            ok = bool(refactorings)
            message = (f"Detected {', '.join(sorted({f.kind for f in refactorings}))}." if ok
                       else "No refactoring detected.")

        return StageResult(
            ok=ok, reason="" if ok else self.reason, message=message,
            log="\n".join(str(f) for f in findings)[:8000],
            outputs={
                "detected": [str(f) for f in refactorings][:50],
                "detectedCount": len(refactorings),
                "expected": expected,
                "matched": matched,
                "filesAnalysed": len(paths),
                "parseErrors": [f.detail for f in broken][:20],
            },
        )


def _changed_python_files(diff_text: str) -> list[str]:
    paths: list[str] = []
    for match in (*DIFF_TARGET.finditer(diff_text), *DIFF_SOURCE.finditer(diff_text)):
        path = match.group("path").strip()
        if path.endswith(".py") and path != "/dev/null" and path not in paths:
            paths.append(path)
    return paths[:MAX_FILES]


def _expected(ctx: EvalContext, config: dict) -> list[str]:
    raw = config.get("expected")
    if raw is None:
        raw = ctx.reference(str(config.get("expected_from", "") or ""))
    if not raw:
        return []
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    return [str(part).strip() for part in raw if str(part).strip()]
