"""SWE-Refactor benchmark plugin (Java).

Prompts follow the SWE-Refactor protocol: one template per refactoring type
(task description, code to refactor, whole-class content, refactoring operation,
and — for move-like refactorings — the project structure). Templates live in
`prompts/` and are operator-editable.

Evaluation is workspace-derived: the agent edits the file(s) in the workspace,
and the AFTER state is read straight from there (the agent's real edits are the
ground truth, already captured in diff.patch). RefactoringMiner compares that
against the dataset's whole-file BEFORE, then the project is compiled and tested.
No self-reported output envelope — weak models are unreliable at duplicating
their work into a side file, and the workspace is authoritative regardless.

Answer-leak prevention: the prompt exposes only an allow-listed before-state
subset of the dataset row; solution fields never reach the workspace or prompt.

Imports ONLY from app.catalog.sdk.
"""
from __future__ import annotations

import json
import tempfile
from functools import lru_cache
from pathlib import Path

from app.catalog.sdk import BenchmarkPlugin, EvalContext, SessionCtx, StageResult, TaskDef

PLUGIN_DIR = Path(__file__).resolve().parent
DATASET = "pure_refactoring_data.json"

TASK_DESCRIPTION = (
    "You are an expert software engineer. You are given a code to be refactored. "
    "The objective is to refactor this code by performing given refactoring operation. "
    "This refactoring will improve code readability, maintainability, and modularity."
)

# refactoring type → prompt template
_TEMPLATES = {
    "Extract Method": "extract_method_baseline_prompt.txt",
    "Inline Method": "inline_method_baseline_prompt.txt",
    "Move Method": "move_method_prompt_baseline.txt",
    "Move And Rename Method": "move_and_rename_method_baseline_prompt.txt",
    "Extract And Move Method": "extract_and_move_method_baseline_prompt.txt",
    "Move And Inline Method": "move_and_inline_baseline_prompt.txt",
}

# before-state fields the prompt may legitimately show (no solution fields)
_ALLOW = ("type", "filePathBefore", "sourceCodeBeforeRefactoring",
          "sourceCodeBeforeForWhole", "classNameBefore", "methodNameBefore",
          "packageNameBefore", "classSignatureBefore")

_MAX_STRUCTURE_FILES = 400


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


def _dataset_path(data_dir: Path) -> Path | None:
    direct = data_dir / DATASET
    if direct.is_file():
        return direct
    return next((p for p in data_dir.rglob(DATASET) if "__MACOSX" not in str(p)), None)


@lru_cache(maxsize=1)
def _rows_by_id(data_dir: str) -> dict[str, dict]:
    """The dataset row payload is looked up by uniqueId rather than embedded in
    tasks.yaml — embedding it produced a 35 MB manifest parsed on every startup."""
    path = _dataset_path(Path(data_dir))
    if path is None:
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {r["uniqueId"]: r for r in rows if r.get("uniqueId")}


def _row(task: TaskDef, data_dir: Path) -> dict:
    uid = task.params.get("uniqueId", "")
    return _rows_by_id(str(data_dir)).get(uid, {})


def _template(ctx: SessionCtx, name: str) -> str:
    """Operator-edited template (Settings) wins over the shipped default."""
    override = Path(ctx.extra.get("prompts_dir", "")) / name if ctx.extra.get("prompts_dir") else None
    if override and override.is_file():
        return override.read_text(encoding="utf-8")
    return (PLUGIN_DIR / "prompts" / name).read_text(encoding="utf-8")


def _scope_prefix(file_path_before: str) -> str:
    parts = [p for p in Path(file_path_before).parts if p]
    if len(parts) >= 3:
        return "/".join(parts[:3])
    return parts[0] if parts else ""


def project_structure(workspace: Path, file_path_before: str) -> str:
    """Java files in the same source root as the target, so a move-like
    refactoring can name a real destination file."""
    prefix = _scope_prefix(file_path_before)
    files = []
    for path in sorted(workspace.rglob("*.java")):
        rel = path.relative_to(workspace).as_posix()
        if not prefix or prefix in rel:
            files.append(rel)
            if len(files) >= _MAX_STRUCTURE_FILES:
                files.append(f"... (truncated at {_MAX_STRUCTURE_FILES} files)")
                break
    return "\n".join(files)


class Plugin(BenchmarkPlugin):
    key = "swe"

    def build_prompt(self, task: TaskDef, ctx: SessionCtx) -> str | None:
        row = _row(task, PLUGIN_DIR / "data")
        if not row:
            return None  # dataset not bootstrapped; platform falls back
        safe = {k: row.get(k) for k in _ALLOW if k in row}
        rtype = safe.get("type", "")
        template = _TEMPLATES.get(rtype)
        if template is None:
            return None
        target = safe.get("filePathBefore", "")
        values = {
            "task_description": TASK_DESCRIPTION,
            "code_to_refactor": str(safe.get("sourceCodeBeforeRefactoring", "")).strip(),
            "class_content": str(safe.get("sourceCodeBeforeForWhole", "")).strip(),
            "refactoring_operation": rtype,
            "file_path_before_refactoring": target,
            "project_structure": project_structure(ctx.workspace, target),
        }
        return _template(ctx, template).format_map(_SafeDict(values))

    def stages(self):
        return {"swe.prepare_candidate": _prepare_candidate, "swe.codebleu": _codebleu}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _prepare_candidate(ctx: EvalContext, config: dict) -> StageResult:
    """Read the agent's edited file(s) from the workspace and stage the
    before/after pair RefactoringMiner needs (published via ctx.shared)."""
    params = ctx.task.params
    rtype = params.get("refactoringType", "")
    target = params.get("filePathBefore", "")
    dest_rel = params.get("filePathAfter", "") or ""
    if not target:
        return StageResult(name="swe.prepare_candidate", ok=False, reason="apply_failed",
                           message="Task has no target file path.")

    row = _row(ctx.task, ctx.data_root)
    before_whole = row.get("sourceCodeBeforeForWhole") or row.get("sourceCodeBeforeRefactoring") or ""
    if not before_whole:
        return StageResult(name="swe.prepare_candidate", ok=False, reason="apply_failed",
                           message="Dataset row not found; run the data bootstrap.")

    tmp = Path(tempfile.mkdtemp(prefix="swe-rm-"))
    before_f = tmp / "before.java"
    before_f.write_text(before_whole, encoding="utf-8")

    if dest_rel and dest_rel != target:  # move-like refactoring
        dest_path = ctx.workspace / dest_rel
        if not dest_path.is_file():
            return StageResult(name="swe.prepare_candidate", ok=False, reason="apply_failed",
                               message=f"Destination file not found in workspace: {dest_rel}")
        after_dest = tmp / "dest_after.java"
        after_dest.write_text(_read(dest_path), encoding="utf-8")
        ctx.shared["rm_args"] = ["-spr", target, str(before_f), dest_rel, str(after_dest), rtype]
        return StageResult(name="swe.prepare_candidate", ok=True,
                           message=f"Prepared move-refactoring inputs from workspace ({dest_rel}).")

    tgt_path = ctx.workspace / target
    if not tgt_path.is_file():
        return StageResult(name="swe.prepare_candidate", ok=False, reason="apply_failed",
                           message=f"Target file not found in workspace: {target}")
    after_f = tmp / "after.java"
    after_f.write_text(_read(tgt_path), encoding="utf-8")
    ctx.shared["rm_args"] = ["-scr", target, str(before_f), str(after_f), rtype]
    return StageResult(name="swe.prepare_candidate", ok=True,
                       message="Prepared single-file refactoring inputs from workspace.")


def _candidate_path(ctx: EvalContext) -> Path | None:
    """The file the agent was asked to refactor, as it stands after the run."""
    params = ctx.task.params
    rel = params.get("filePathAfter") or params.get("filePathBefore") or ""
    path = ctx.workspace / rel if rel else None
    return path if path and path.is_file() else None


def _codebleu(ctx: EvalContext, config: dict) -> StageResult:
    """Similarity of the agent's file to the dataset's reference refactoring.

    A capture stage: it measures, it does not gate. CodeBLEU blends n-gram,
    weighted n-gram, AST and data-flow match, so an agent that reaches the same
    behaviour by a different route still scores well — which is why a low score
    is a signal to read the diff, not a verdict on its own.

    Compared whole-file against `sourceCodeAfterForWhole`. The original study
    scored the extracted snippet from the agent's answer; this platform derives
    the candidate from the workspace instead (there is no answer envelope), and
    whole-file is the only comparison both sides can supply honestly.
    """
    name = "swe.codebleu"
    try:
        from codebleu import calc_codebleu
    except ImportError:
        return StageResult(name=name, ok=True, message="CodeBLEU unavailable (library not installed).")

    row = _row(ctx.task, ctx.data_root)
    reference = str(row.get("sourceCodeAfterForWhole") or "").strip()
    path = _candidate_path(ctx)
    if not reference or path is None:
        return StageResult(name=name, ok=True, message="CodeBLEU skipped (no reference or candidate).")

    try:
        m = calc_codebleu([reference], [_read(path)], lang="java")
    except Exception as exc:                       # a scorer must never fail a run
        return StageResult(name=name, ok=True, message=f"CodeBLEU failed: {exc}")

    score = float(m["codebleu"])
    return StageResult(
        name=name, ok=True,
        message=f"CodeBLEU {score:.3f} against the reference refactoring.",
        outputs={
            "codebleu": round(score, 4),
            "codebleuNgram": round(float(m["ngram_match_score"]), 4),
            "codebleuWeightedNgram": round(float(m["weighted_ngram_match_score"]), 4),
            "codebleuSyntax": round(float(m["syntax_match_score"]), 4),
            "codebleuDataflow": round(float(m["dataflow_match_score"]), 4),
        },
    )
