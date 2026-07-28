"""How close the agent's file is to a reference version of it.

CodeBLEU blends n-gram, weighted n-gram, syntax-tree and data-flow match, so an
agent that reaches the same behaviour by another route still scores well. It is
recorded, never gating: a low score is a reason to read the diff, not a verdict.

Both sides come from the benchmark: it publishes the reference text and the path
of the candidate while preparing the workspace, and this compares them whole-file.
"""
from __future__ import annotations

from pathlib import Path

from app.catalog.sdk import (
    EvalContext,
    EvaluationPlugin,
    MetricOption,
    MetricSpec,
    StageResult,
)

LANGUAGES = ("java", "python", "c_sharp", "c", "cpp", "javascript", "php", "go", "ruby", "rust")


class Plugin(EvaluationPlugin):
    key = "codebleu"

    spec = MetricSpec(
        title="CodeBLEU similarity",
        summary=("Scores the agent's file against a reference version of the same file. Recorded, "
                 "never gating: reaching the same result another way still scores well."),
        requires="the codebleu library, plus a reference the benchmark publishes",
        gates=False,
        options=(
            MetricOption(key="reference_from", label="Reference text", type="reference",
                         default="shared.reference_text",
                         help="Where the reference version comes from. The benchmark publishes it "
                              "while preparing the workspace."),
            MetricOption(key="candidate_from", label="Candidate file", type="reference",
                         default="shared.candidate_path",
                         help="Path of the file to score, absolute or relative to the workspace."),
            MetricOption(key="language", label="Language", type="choice", default="java",
                         choices=LANGUAGES,
                         help="The grammar CodeBLEU parses both sides with."),
        ),
        outputs=("codebleu", "codebleuNgram", "codebleuWeightedNgram",
                 "codebleuSyntax", "codebleuDataflow"),
    )

    def availability(self) -> tuple[bool, str]:
        try:
            import codebleu  # noqa: F401
        except ImportError:
            return False, "the codebleu library is not installed"
        return True, ""

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        try:
            from codebleu import calc_codebleu
        except ImportError:
            return StageResult(ok=True, message="CodeBLEU unavailable (library not installed).")

        reference = str(ctx.reference(config.get("reference_from", "shared.reference_text")) or "").strip()
        candidate = _candidate(ctx, config)
        if not reference or candidate is None:
            return StageResult(ok=True, message="CodeBLEU skipped (no reference or candidate).")

        text = candidate.read_text(encoding="utf-8", errors="replace")
        try:
            scores = calc_codebleu([reference], [text], lang=str(config.get("language", "java")))
        except Exception as exc:                  # a recorded score must never fail a run
            return StageResult(ok=True, message=f"CodeBLEU failed: {exc}")

        score = float(scores["codebleu"])
        return StageResult(
            ok=True,
            message=f"CodeBLEU {score:.3f} against the reference.",
            outputs={
                "codebleu": round(score, 4),
                "codebleuNgram": round(float(scores["ngram_match_score"]), 4),
                "codebleuWeightedNgram": round(float(scores["weighted_ngram_match_score"]), 4),
                "codebleuSyntax": round(float(scores["syntax_match_score"]), 4),
                "codebleuDataflow": round(float(scores["dataflow_match_score"]), 4),
            },
        )


def _candidate(ctx: EvalContext, config: dict) -> Path | None:
    raw = ctx.reference(config.get("candidate_from", "shared.candidate_path"))
    if not raw:
        return None
    path = Path(str(raw))
    if not path.is_absolute():
        path = ctx.workspace / path
    return path if path.is_file() else None
