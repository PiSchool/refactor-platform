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

from app.catalog.sdk import (
    BenchmarkPlugin,
    EvalContext,
    MetricSpec,
    PromptSpec,
    PromptVariable,
    SessionCtx,
    StageResult,
    TaskDef,
)

PLUGIN_DIR = Path(__file__).resolve().parent
DATASET = "pure_refactoring_data.json"

TASK_DESCRIPTION = (
    "You are an expert software engineer. You are given a code to be refactored. "
    "The objective is to refactor this code by performing given refactoring operation. "
    "This refactoring will improve code readability, maintainability, and modularity."
)

# refactoring type → prompt template
_TEMPLATES = {
    "Extract Method": "extract_method.md",
    "Inline Method": "inline_method.md",
    "Move Method": "move_method.md",
    "Move And Rename Method": "move_and_rename_method.md",
    "Extract And Move Method": "extract_and_move_method.md",
    "Move And Inline Method": "move_and_inline_method.md",
}

#: What `build_prompt` substitutes into whichever template the task selects.
#: Without the code or the operation the task is undefined, so an edit that drops
#: either is refused rather than sent to an agent.
_PROMPT_VARIABLES = (
    PromptVariable("code_to_refactor", "the method to be refactored, as it stands"),
    PromptVariable("refactoring_operation", "the refactoring the task asks for"),
    PromptVariable("task_description", "the benchmark's standing instruction", required=False),
    PromptVariable("class_content", "the whole file the method lives in", required=False),
    PromptVariable("file_path_before_refactoring", "that file's path in the repository",
                   required=False),
    PromptVariable("project_structure", "the surrounding package tree, for move-like operations",
                   required=False),
)

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

    def prepare(self, ctx: EvalContext) -> StageResult:
        return _prepare_candidate(ctx)

    def describe_preparation(self) -> MetricSpec:
        return MetricSpec(
            title="Prepare the detector's inputs",
            summary=("Pairs the agent's edited file with the dataset's before-state, which is "
                     "what RefactoringMiner is then run on, and publishes the dataset's own "
                     "refactoring for the similarity score. Fails when the agent changed no "
                     "Java file."),
            requires="the SWE-Refactor dataset in the benchmark's data directory",
            gates=False,
            outputs=("rm_args", "reference_text", "candidate_path"),
        )

    def describe_prompts(self):
        return {
            name: PromptSpec(
                applies_to=f"tasks whose refactoring type is {rtype}",
                syntax="format",
                variables=_PROMPT_VARIABLES,
            )
            for rtype, name in _TEMPLATES.items()
        }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _prepare_candidate(ctx: EvalContext) -> StageResult:
    """Stage what this benchmark's metrics compare, and publish it.

    RefactoringMiner needs the dataset's whole-file before-state paired with the
    file as the agent left it; the similarity score needs the dataset's own
    refactoring and the same candidate. Both are read from the workspace, which
    is authoritative: the agent's edits are the ground truth.
    """
    params = ctx.task.params
    rtype = params.get("refactoringType", "")
    target = params.get("filePathBefore", "")
    dest_rel = params.get("filePathAfter", "") or ""
    if not target:
        return StageResult(ok=False, reason="apply_failed",
                           message="Task has no target file path.")

    row = _row(ctx.task, ctx.data_root)
    before_whole = row.get("sourceCodeBeforeForWhole") or row.get("sourceCodeBeforeRefactoring") or ""
    if not before_whole:
        return StageResult(ok=False, reason="apply_failed",
                           message="Dataset row not found; run the data bootstrap.")

    # The reference is the dataset's own refactoring of the same file. Compared
    # whole-file: the study scored the snippet an agent reported, this platform
    # derives the candidate from the workspace, and whole-file is the only
    # comparison both sides can supply honestly.
    ctx.shared["reference_text"] = str(row.get("sourceCodeAfterForWhole") or "")

    tmp = Path(tempfile.mkdtemp(prefix="swe-rm-"))
    before_f = tmp / "before.java"
    before_f.write_text(before_whole, encoding="utf-8")

    if dest_rel and dest_rel != target:  # move-like refactoring
        dest_path = ctx.workspace / dest_rel
        if not dest_path.is_file():
            return StageResult(ok=False, reason="apply_failed",
                               message=f"Destination file not found in workspace: {dest_rel}")
        after_dest = tmp / "dest_after.java"
        after_dest.write_text(_read(dest_path), encoding="utf-8")
        ctx.shared["rm_args"] = ["-spr", target, str(before_f), dest_rel, str(after_dest), rtype]
        ctx.shared["candidate_path"] = str(dest_path)
        return StageResult(ok=True,
                           message=f"Prepared move-refactoring inputs from workspace ({dest_rel}).",
                           outputs={"candidatePath": dest_rel, "refactoringType": rtype})

    tgt_path = ctx.workspace / target
    if not tgt_path.is_file():
        return StageResult(ok=False, reason="apply_failed",
                           message=f"Target file not found in workspace: {target}")
    after_f = tmp / "after.java"
    after_f.write_text(_read(tgt_path), encoding="utf-8")
    ctx.shared["rm_args"] = ["-scr", target, str(before_f), str(after_f), rtype]
    ctx.shared["candidate_path"] = str(tgt_path)
    return StageResult(ok=True,
                       message="Prepared single-file refactoring inputs from workspace.",
                       outputs={"candidatePath": target, "refactoringType": rtype})
