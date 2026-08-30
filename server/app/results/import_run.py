"""Hardened, atomic recreation of a run (rows + artifacts) from a platform ZIP.

Nothing here trusts the archive. The flow is strictly:

1. Validate the whole central directory and archive schema *before* any
   bytes are decompressed (`app.results.archive_safety` does the low-level
   work; this module owns the run-shaped policy on top of it).
2. Cross-check the manifest against `summary.json`, require a unique
   inventory entry for every — and only — archived artifact, verify 64-hex
   hashes / sizes / media types, and reject any relative path that is not in
   the positive evidence catalog.
3. Only then stream-extract into a unique, same-filesystem `.importing-*`
   staging directory under `outputs/runs`, remap every export-local id to a
   fresh one, and lay the evidence out at its intended final path.
4. In one DB transaction: add all rows/pointers, flush, atomically rename
   staging to the final run directory, then commit. Any failure rolls the
   transaction back and removes both staging and any renamed final directory,
   so a partial run is never queryable.
"""
from __future__ import annotations

import math
import os
import re
import shutil
import tempfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import engine as db_engine
from app.db.models import (
    AgentSession,
    AgentTool,
    Benchmark,
    Run,
    RunTask,
    Task,
    TaskResult,
    new_id,
    utcnow,
)
from app.execution.setups import ARCHIVE_SETUPS, SETUPS
from app.results.archive_safety import (
    ArchiveTooLarge,
    ExpectedMember,
    ImportLimits,
    build_extraction_plan,
    extract_plan,
    read_json,
)
from app.results.bundle import FORMAT, RunManifest


class ImportRejected(Exception):
    """The archive is well-formed enough to open but violates import policy.

    The API layer maps this (and non-`ArchiveTooLarge` archive-safety errors)
    to HTTP 422; `ArchiveTooLarge` maps to 413.
    """


# --- Positive evidence catalog -------------------------------------------
#
# Mirrors the exporter's catalog in `app.results.artifacts`: the only relative
# paths that may appear under `artifacts/tasks/<task-XXXX>/…`. Anything else —
# `workspace/`, `.git/`, private state — is rejected outright.

_TASK_FOLDER = re.compile(r"^task-\d{4}$")
_SESSION_FOLDER = re.compile(r"^session-\d{4}$")
_RUN_ID = re.compile(r"^[0-9a-f]{32}$")
_STEM = r"[A-Za-z0-9_-]{1,128}"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+:/-]{0,299}$")
_TASK_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+:/#-]{0,299}$")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_IMPORT_MARKER = ".importing"

_STATIC_TASK_MEDIA: dict[str, str] = {
    "prompt.md": "text/markdown",
    "response.md": "text/markdown",
    "diff.patch": "text/x-diff",
    "workspace_meta.json": "application/json",
    "retrieval/context.md": "text/markdown",
    "retrieval/queries.json": "application/json",
    "retrieval/hits.json": "application/json",
    "retrieval/provenance.json": "application/json",
    "retrieval/invocations.jsonl": "application/x-ndjson",
    "study/source-table.md": "text/markdown",
    "study/source.csv": "text/csv",
}
_SESSION_FILE_MEDIA: dict[str, str] = {
    "terminal.log": "text/plain",
    "transcript.txt": "text/plain",
    "events.jsonl": "application/x-ndjson",
}
_EVAL_LOG = re.compile(rf"^eval/{_STEM}\.log$")
_SELF_RESULT = re.compile(r"^eval/self-checks/attempt-\d{4}/result\.json$")
_SELF_LOG = re.compile(rf"^eval/self-checks/attempt-\d{{4}}/logs/{_STEM}\.log$")

# Terminal statuses only: an active run/task/session cannot be imported.
_TERMINAL_RUN = {"completed", "stopped", "failed", "error"}
_TERMINAL_TASK = {"passed", "failed", "error", "stopped", "timed_out", "skipped"}
_TERMINAL_SESSION = {"ended", "completed", "failed", "stopped", "killed", "error"}

_MANIFEST_KEYS = {
    "format", "createdAt", "sourceRunId", "benchmark", "setup",
    "agentTool", "status", "taskCount", "artifacts",
}
_SUMMARY_KEYS = {"run", "tasks"}
_RUN_KEYS = {
    "id", "status", "benchmark", "setup", "agentTool", "model",
    "taskTimeoutSeconds", "config", "counts", "passRate", "queuedAt",
    "startedAt", "finishedAt",
}
_TASK_KEYS = {
    "id", "taskKey", "title", "ordinal", "status", "timeoutSeconds",
    "startedAt", "finishedAt", "params", "result", "session", "artifacts",
}
_RESULT_KEYS = {
    "passed", "reason", "durationSeconds", "agentSeconds", "evaluateSeconds",
    "tokensInput", "tokensOutput", "model", "metrics", "details",
}
_SESSION_KEYS = {"id", "role", "status", "startedAt", "finishedAt", "artifacts"}
_ARTIFACT_REF_KEYS = {
    "key", "available", "mediaType", "sizeBytes",
}
_COUNTS_KEYS = {"total", "passed", "failed", "timedOut", "pending"}


@dataclass(frozen=True)
class _Placement:
    """Where one archived artifact member belongs in the recreated run."""

    task_folder: str
    session_folder: str | None  # None → task-level evidence
    rest: str                   # path under the task dir, or session filename
    media_type: str


def _task_media_type(rest: str) -> str | None:
    if rest in _STATIC_TASK_MEDIA:
        return _STATIC_TASK_MEDIA[rest]
    if _EVAL_LOG.fullmatch(rest):
        return "text/plain"
    if rest == "eval/self-checks/limit-reached.json":
        return "application/json"
    if _SELF_RESULT.fullmatch(rest):
        return "application/json"
    if _SELF_LOG.fullmatch(rest):
        return "text/plain"
    return None


def _classify(path: str) -> _Placement:
    """Map an archive member path to a catalogued placement, or reject it."""
    parts = path.split("/")
    if len(parts) < 4 or parts[0] != "artifacts" or parts[1] != "tasks":
        raise ImportRejected(f"artifact outside the evidence catalog: {path!r}")
    task_folder = parts[2]
    if not _TASK_FOLDER.fullmatch(task_folder):
        raise ImportRejected(f"invalid task folder in artifact path: {path!r}")
    rest_parts = parts[3:]
    if rest_parts and rest_parts[0] == "sessions":
        if len(rest_parts) != 3:
            raise ImportRejected(f"malformed session artifact path: {path!r}")
        session_folder, filename = rest_parts[1], rest_parts[2]
        if not _SESSION_FOLDER.fullmatch(session_folder):
            raise ImportRejected(f"invalid session folder in artifact path: {path!r}")
        media = _SESSION_FILE_MEDIA.get(filename)
        if media is None:
            raise ImportRejected(f"session artifact not in catalog: {path!r}")
        return _Placement(task_folder, session_folder, filename, media)
    rest = "/".join(rest_parts)
    media = _task_media_type(rest)
    if media is None:
        raise ImportRejected(f"task artifact not in evidence catalog: {path!r}")
    return _Placement(task_folder, None, rest, media)


def _is_source_path(value: str) -> bool:
    return (
        (value.startswith("/") and not value.startswith("/api/"))
        or bool(_WINDOWS_ABSOLUTE.match(value))
    )


def _reject_embedded_source_paths(value: Any, *, reject_fields: bool = True) -> None:
    """Refuse any absolute filesystem path smuggled into a JSON string value."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = re.sub(r"[^a-z]", "", str(key).lower())
            if reject_fields and (normalized.endswith("path") or normalized.endswith("directory")
                    or normalized.endswith("root") or normalized in {"cwd", "workdir"}):
                raise ImportRejected(f"source filesystem field embedded in import JSON: {key!r}")
            _reject_embedded_source_paths(item, reject_fields=reject_fields)
    elif isinstance(value, list):
        for item in value:
            _reject_embedded_source_paths(item, reject_fields=reject_fields)
    elif isinstance(value, str) and _is_source_path(value):
        raise ImportRejected(f"source filesystem path embedded in import JSON: {value!r}")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ImportRejected("non-finite number embedded in import JSON")


def _valid_key(value: Any) -> bool:
    return isinstance(value, str) and bool(_KEY.fullmatch(value))


def _valid_task_key(value: Any) -> bool:
    return isinstance(value, str) and bool(_TASK_KEY.fullmatch(value))


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _require_object_keys(value: Any, allowed: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise ImportRejected(f"{label} must be a JSON object")
    missing = allowed - set(value)
    extra = set(value) - allowed
    if missing:
        raise ImportRejected(f"{label} is missing keys: {sorted(missing)}")
    if extra:
        raise ImportRejected(f"{label} has unexpected keys: {sorted(extra)}")
    return value


def _require_text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value) or len(value) > 4096:
        raise ImportRejected(f"{label} must be a bounded string")
    return value


def _require_nonnegative_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ImportRejected(f"{label} must be a non-negative integer")
    return value


def _require_nonnegative_number(value: Any, label: str) -> float:
    if (not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(float(value)) or value < 0):
        raise ImportRejected(f"{label} must be a finite non-negative number")
    return float(value)


def _validate_optional_datetime(value: Any, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise ImportRejected(f"{label} must be an ISO-8601 string or null")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ImportRejected(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ImportRejected(f"{label} must include a timezone")


def _validate_plugin_ref(value: Any, label: str, *, language: bool = False) -> dict:
    keys = {"key", "name"} | ({"language"} if language else set())
    ref = _require_object_keys(value, keys, label)
    for field in keys:
        _require_text(ref[field], f"{label}.{field}")
    if not _valid_key(ref["key"]):
        raise ImportRejected(f"invalid {label} key: {ref['key']!r}")
    return ref


def _validate_artifact_refs(value: Any, label: str) -> None:
    if not isinstance(value, list):
        raise ImportRejected(f"{label} must be a list")
    seen: set[str] = set()
    for index, item in enumerate(value):
        ref = _require_object_keys(item, _ARTIFACT_REF_KEYS, f"{label}[{index}]")
        key = _require_text(ref["key"], f"{label}[{index}].key")
        if key in seen:
            raise ImportRejected(f"{label} contains duplicate key {key!r}")
        seen.add(key)
        if not isinstance(ref["available"], bool):
            raise ImportRejected(f"{label}[{index}].available must be boolean")
        _require_text(ref["mediaType"], f"{label}[{index}].mediaType")
        _require_nonnegative_int(ref["sizeBytes"], f"{label}[{index}].sizeBytes")


def _validate_result(value: Any, label: str) -> None:
    if value is None:
        return
    result = _require_object_keys(value, _RESULT_KEYS, label)
    if not isinstance(result["passed"], bool):
        raise ImportRejected(f"{label}.passed must be boolean")
    if result["reason"] is not None:
        _require_text(result["reason"], f"{label}.reason", allow_empty=True)
    for field in ("durationSeconds", "agentSeconds", "evaluateSeconds"):
        _require_nonnegative_number(result[field], f"{label}.{field}")
    for field in ("tokensInput", "tokensOutput"):
        _require_nonnegative_int(result[field], f"{label}.{field}")
    _require_text(result["model"], f"{label}.model", allow_empty=True)
    for field in ("metrics", "details"):
        if not isinstance(result[field], dict):
            raise ImportRejected(f"{label}.{field} must be a JSON object")


def _read_member_json(zf: zipfile.ZipFile, name: str, limits: ImportLimits) -> Any:
    try:
        with zf.open(name) as handle:
            return read_json(handle, max_bytes=limits.max_json_bytes,
                             chunk_bytes=limits.chunk_bytes)
    except ArchiveTooLarge:
        raise
    except (KeyError, JSONDecodeError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
        raise ImportRejected(f"{name} is missing or malformed: {exc}") from exc


def _validate_top_level(member_names: set[str]) -> None:
    allowed = {"manifest.json", "summary.json", "results.csv"}
    for name in member_names:
        if name in allowed or name.startswith("artifacts/"):
            continue
        raise ImportRejected(f"unexpected archive member: {name!r}")


@dataclass(frozen=True)
class _Provenance:
    format: str
    source_run_id: str
    created_at: str | None


def _validate_manifest_types(manifest: dict) -> None:
    for field in ("format", "createdAt", "sourceRunId", "status"):
        _require_text(manifest.get(field), f"manifest.{field}")
    if (not isinstance(manifest.get("taskCount"), int)
            or isinstance(manifest["taskCount"], bool) or manifest["taskCount"] < 0):
        raise ImportRejected("manifest.taskCount must be a non-negative integer")
    if not _RUN_ID.fullmatch(manifest["sourceRunId"]):
        raise ImportRejected("manifest.sourceRunId is not a platform run identity")
    _validate_optional_datetime(manifest["createdAt"], "manifest.createdAt")

    for label in ("benchmark", "setup", "agentTool"):
        ref = _require_object_keys(
            manifest.get(label), {"key", "name"}, f"manifest.{label}",
        )
        if not _valid_key(ref["key"]):
            raise ImportRejected(f"invalid manifest.{label}.key: {ref['key']!r}")
        _require_text(ref["name"], f"manifest.{label}.name")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ImportRejected("manifest.artifacts must be a list")
    for index, item in enumerate(artifacts):
        entry = _require_object_keys(
            item, {"path", "sizeBytes", "sha256", "mediaType"},
            f"manifest.artifacts[{index}]",
        )
        _require_text(entry["path"], f"manifest.artifacts[{index}].path")
        _require_nonnegative_int(
            entry["sizeBytes"], f"manifest.artifacts[{index}].sizeBytes",
        )
        _require_text(entry["sha256"], f"manifest.artifacts[{index}].sha256")
        _require_text(entry["mediaType"], f"manifest.artifacts[{index}].mediaType")


def _validate_manifest(
    manifest_raw: Any,
    summary: dict,
    member_names: set[str],
) -> tuple[_Provenance, dict[str, ExpectedMember], list[str]]:
    if not isinstance(manifest_raw, dict):
        raise ImportRejected("manifest.json must be a JSON object")
    _reject_embedded_source_paths(manifest_raw, reject_fields=False)
    extra = set(manifest_raw) - _MANIFEST_KEYS
    if extra:
        raise ImportRejected(f"manifest has unexpected keys: {sorted(extra)}")
    missing = _MANIFEST_KEYS - set(manifest_raw)
    if missing:
        raise ImportRejected(f"manifest is missing keys: {sorted(missing)}")
    _validate_manifest_types(manifest_raw)
    try:
        manifest = RunManifest.model_validate(manifest_raw)
    except ValidationError as exc:
        raise ImportRejected(f"manifest failed schema validation: {exc}") from exc
    if manifest.format != FORMAT:
        raise ImportRejected(f"unsupported manifest format: {manifest.format!r}")

    run_meta = summary.get("run")
    if not isinstance(run_meta, dict):
        raise ImportRejected("summary.json is missing its run object")
    tasks = summary.get("tasks")
    if not isinstance(tasks, list):
        raise ImportRejected("summary.json is missing its tasks list")

    if manifest.status != run_meta.get("status"):
        raise ImportRejected("manifest/summary status mismatch")
    if manifest.task_count != len(tasks):
        raise ImportRejected("manifest/summary taskCount mismatch")
    if manifest.source_run_id != run_meta.get("id"):
        raise ImportRejected("manifest/summary sourceRunId mismatch")
    for label, ref in (
        ("benchmark", manifest.benchmark),
        ("setup", manifest.setup),
        ("agentTool", manifest.agent_tool),
    ):
        if ref.key != (run_meta.get(label) or {}).get("key"):
            raise ImportRejected(f"manifest/summary {label} mismatch")

    manifest_paths = [entry.path for entry in manifest.artifacts]
    if len(manifest_paths) != len(set(manifest_paths)):
        raise ImportRejected("manifest lists a duplicate artifact path")
    zip_artifacts = {name for name in member_names if name.startswith("artifacts/")}
    if set(manifest_paths) != zip_artifacts:
        raise ImportRejected(
            "manifest inventory does not match the archive's artifact members"
        )

    expected: dict[str, ExpectedMember] = {}
    for entry in manifest.artifacts:
        if not _HEX64.fullmatch(entry.sha256):
            raise ImportRejected(f"artifact hash is not 64 hex chars: {entry.path!r}")
        if entry.size_bytes < 0:
            raise ImportRejected(f"artifact declares a negative size: {entry.path!r}")
        placement = _classify(entry.path)
        if placement.media_type != entry.media_type:
            raise ImportRejected(f"artifact media type mismatch for {entry.path!r}")
        expected[entry.path] = ExpectedMember(
            size_bytes=entry.size_bytes, sha256=entry.sha256,
        )

    provenance = _Provenance(
        format=manifest.format,
        source_run_id=manifest.source_run_id,
        created_at=manifest.created_at.isoformat(),
    )
    return provenance, expected, sorted(manifest_paths)


@dataclass(frozen=True)
class _ValidatedSummary:
    run: dict
    tasks: list[dict]
    benchmark_key: str
    setup_key: str
    agent_tool_key: str


def _validate_summary(summary: dict) -> _ValidatedSummary:
    _reject_embedded_source_paths(summary)
    summary = _require_object_keys(summary, _SUMMARY_KEYS, "summary.json")
    run_meta = _require_object_keys(summary["run"], _RUN_KEYS, "summary.run")
    source_id = run_meta["id"]
    if not isinstance(source_id, str) or not _RUN_ID.fullmatch(source_id):
        raise ImportRejected(f"invalid source run identifier: {source_id!r}")
    status = run_meta.get("status")
    if status not in _TERMINAL_RUN:
        raise ImportRejected(f"run status is not importable: {status!r}")

    benchmark = _validate_plugin_ref(run_meta["benchmark"], "summary.run.benchmark", language=True)
    setup = _validate_plugin_ref(run_meta["setup"], "summary.run.setup")
    agent_tool = _validate_plugin_ref(run_meta["agentTool"], "summary.run.agentTool")
    benchmark_key = benchmark["key"]
    setup_key = setup["key"]
    agent_tool_key = agent_tool["key"]
    for label, key in (
        ("benchmark", benchmark_key),
        ("setup", setup_key),
        ("agentTool", agent_tool_key),
    ):
        if not _valid_key(key):
            raise ImportRejected(f"invalid {label} identifier: {key!r}")

    _require_text(run_meta["model"], "summary.run.model", allow_empty=True)
    timeout = _require_nonnegative_int(
        run_meta["taskTimeoutSeconds"], "summary.run.taskTimeoutSeconds",
    )
    if timeout == 0:
        raise ImportRejected("summary.run.taskTimeoutSeconds must be positive")
    if not isinstance(run_meta["config"], dict):
        raise ImportRejected("summary.run.config must be a JSON object")
    counts = _require_object_keys(run_meta["counts"], _COUNTS_KEYS, "summary.run.counts")
    for field in _COUNTS_KEYS:
        _require_nonnegative_int(counts[field], f"summary.run.counts.{field}")
    pass_rate = _require_nonnegative_number(run_meta["passRate"], "summary.run.passRate")
    if pass_rate > 1:
        raise ImportRejected("summary.run.passRate cannot exceed 1")
    for field in ("queuedAt", "startedAt", "finishedAt"):
        _validate_optional_datetime(run_meta[field], f"summary.run.{field}")
    if run_meta["queuedAt"] is None:
        raise ImportRejected("summary.run.queuedAt is required")

    tasks = summary["tasks"]
    if not isinstance(tasks, list):
        raise ImportRejected("summary.json is missing its tasks list")
    if counts["total"] != len(tasks):
        raise ImportRejected("summary task count does not match run counts.total")

    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    seen_ordinals: set[int] = set()
    for index, item in enumerate(tasks):
        task = _require_object_keys(item, _TASK_KEYS, f"summary.tasks[{index}]")
        folder = task["id"]
        if not isinstance(folder, str) or not _TASK_FOLDER.fullmatch(folder):
            raise ImportRejected(f"invalid task identifier: {folder!r}")
        task_key = task["taskKey"]
        if not _valid_task_key(task_key):
            raise ImportRejected(f"invalid task key: {task_key!r}")
        _require_text(task["title"], f"summary.tasks[{index}].title", allow_empty=True)
        ordinal = _require_nonnegative_int(task["ordinal"], f"summary.tasks[{index}].ordinal")
        task_status = task["status"]
        if task_status not in _TERMINAL_TASK:
            raise ImportRejected(f"task status is not importable: {task_status!r}")
        task_timeout = _require_nonnegative_int(
            task["timeoutSeconds"], f"summary.tasks[{index}].timeoutSeconds",
        )
        if task_timeout == 0:
            raise ImportRejected(f"summary.tasks[{index}].timeoutSeconds must be positive")
        for field in ("startedAt", "finishedAt"):
            _validate_optional_datetime(task[field], f"summary.tasks[{index}].{field}")
        if not isinstance(task["params"], dict):
            raise ImportRejected(f"summary.tasks[{index}].params must be a JSON object")
        _validate_result(task["result"], f"summary.tasks[{index}].result")
        _validate_artifact_refs(task["artifacts"], f"summary.tasks[{index}].artifacts")
        if folder in seen_ids:
            raise ImportRejected(f"duplicate task id: {folder!r}")
        if task_key in seen_keys:
            raise ImportRejected(f"duplicate task key: {task_key!r}")
        if ordinal in seen_ordinals:
            raise ImportRejected(f"duplicate task ordinal: {ordinal!r}")
        seen_ids.add(folder)
        seen_keys.add(task_key)
        seen_ordinals.add(ordinal)

        session = task["session"]
        if session is not None:
            session = _require_object_keys(
                session, _SESSION_KEYS, f"summary.tasks[{index}].session",
            )
            session_id = session["id"]
            if not isinstance(session_id, str) or not _SESSION_FOLDER.fullmatch(session_id):
                raise ImportRejected(f"invalid session identifier: {session_id!r}")
            if session["role"] != "primary":
                raise ImportRejected(f"unsupported session role: {session['role']!r}")
            session_status = session["status"]
            if session_status not in _TERMINAL_SESSION:
                raise ImportRejected(f"session status is not importable: {session_status!r}")
            for field in ("startedAt", "finishedAt"):
                _validate_optional_datetime(
                    session[field], f"summary.tasks[{index}].session.{field}",
                )
            _validate_artifact_refs(
                session["artifacts"], f"summary.tasks[{index}].session.artifacts",
            )

    if seen_ordinals != set(range(len(tasks))):
        raise ImportRejected("task ordinals must be contiguous from zero")

    return _ValidatedSummary(
        run=run_meta,
        tasks=tasks,
        benchmark_key=benchmark_key,
        setup_key=setup_key,
        agent_tool_key=agent_tool_key,
    )


# --- Failure-injection seams ---------------------------------------------
#
# Tests monkeypatch these to force a deterministic failure at exactly the
# rename or commit boundary and assert the transaction leaves nothing behind.

def _rename_staging(staging: Path, final: Path) -> None:
    """Atomically promote validated staging to the final run directory."""
    os.replace(staging, final)


async def _commit_import(session: AsyncSession) -> None:
    await session.commit()


def _cleanup_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def cleanup_abandoned_imports() -> None:
    """Remove leftover staging from an interrupted import.

    Only direct `outputs/runs/.importing-*` entries are touched, and symlinks
    are removed as links (never followed), so this can never delete anything
    outside the staging namespace. Safe to call on every startup.
    """
    runs_dir = get_settings().outputs_dir / "runs"
    try:
        entries = list(os.scandir(runs_dir))
    except (FileNotFoundError, NotADirectoryError):
        return
    for entry in entries:
        if not entry.name.startswith(".importing-"):
            continue
        path = Path(entry.path)
        try:
            if entry.is_symlink():
                path.unlink()
            elif entry.is_dir(follow_symlinks=False):
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink()
        except OSError:
            pass


async def cleanup_uncommitted_imports() -> None:
    """Reconcile run directories promoted immediately before a process exit.

    A marker survives the narrow rename-to-commit crash window. Once the
    database is available at startup, directories without a committed row are
    removed; markers for successfully committed runs are simply cleared.
    """
    runs_dir = get_settings().outputs_dir / "runs"
    try:
        entries = list(os.scandir(runs_dir))
    except (FileNotFoundError, NotADirectoryError):
        return

    candidates: dict[str, Path] = {}
    for entry in entries:
        if (not _RUN_ID.fullmatch(entry.name) or entry.is_symlink()
                or not entry.is_dir(follow_symlinks=False)):
            continue
        run_dir = Path(entry.path)
        marker = run_dir / _IMPORT_MARKER
        if marker.is_symlink():
            try:
                marker.unlink()
            except OSError:
                pass
            continue
        if marker.is_file():
            candidates[entry.name] = run_dir
    if not candidates:
        return

    async with db_engine.session_factory()() as session:
        committed = set((await session.execute(
            select(Run.id).where(Run.id.in_(candidates))
        )).scalars())
    for run_id, run_dir in candidates.items():
        if run_id in committed:
            try:
                (run_dir / _IMPORT_MARKER).unlink()
            except OSError:
                pass
        else:
            _cleanup_dir(run_dir)


async def import_archive(archive_path: Path, *, limits: ImportLimits | None = None) -> str:
    """Validate and atomically import a run export; return the new run id.

    Raises `ArchiveTooLarge` for size violations (→ HTTP 413) and
    `ImportRejected`/`ArchiveSafetyError` for malformed or policy-violating
    archives (→ HTTP 422). On any failure nothing is committed and no staging
    or final directory is left on disk.
    """
    settings = get_settings()
    limits = limits or settings.import_limits
    archive_path = Path(archive_path)

    # 1. Central-directory validation (reads no member bytes) + required names.
    probe = build_extraction_plan(
        archive_path,
        settings.outputs_dir / "runs",
        limits=limits,
        required_names=("manifest.json", "summary.json", "results.csv"),
    )
    member_names = {m.relative_path for m in probe.members if not m.is_dir}
    _validate_top_level(member_names)

    # 2. Read the structured documents (bounded) and validate the schema.
    with zipfile.ZipFile(archive_path) as zf:
        summary = _read_member_json(zf, "summary.json", limits)
        manifest_raw = _read_member_json(zf, "manifest.json", limits)
    if not isinstance(summary, dict):
        raise ImportRejected("summary.json must be a JSON object")

    provenance, expected, artifact_paths = _validate_manifest(
        manifest_raw, summary, member_names,
    )
    valid = _validate_summary(summary)

    # 3. Stage and verify the filesystem payload before opening a DB transaction.
    session: AsyncSession | None = None
    staging: Path | None = None
    final_dir: Path | None = None
    try:
        # 4. Extract into unique, same-filesystem staging, then generate fresh
        # identities and remap the export-local layout.
        runs_dir = settings.outputs_dir / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        while True:
            run_id = new_id()
            final_dir = runs_dir / run_id
            if not final_dir.exists():
                break
        staging = Path(tempfile.mkdtemp(prefix=".importing-", dir=runs_dir))
        extract_root = staging / ".extract"

        plan = build_extraction_plan(
            archive_path, extract_root, limits=limits, expected=expected,
        )
        extract_plan(plan)  # streams every member, verifying size/hash as it writes

        new_task_ids = {task["id"]: new_id() for task in valid.tasks}
        session_ids: dict[tuple[str, str], str] = {}
        task_files: dict[str, dict[str, Path]] = defaultdict(dict)
        session_files: dict[tuple[str, str], dict[str, Path]] = defaultdict(dict)

        for path in artifact_paths:
            placement = _classify(path)
            if placement.task_folder not in new_task_ids:
                raise ImportRejected(f"artifact references unknown task folder: {path!r}")
            new_rt_id = new_task_ids[placement.task_folder]
            if placement.session_folder is not None:
                key = (placement.task_folder, placement.session_folder)
                new_sess_id = session_ids.setdefault(key, new_id())
                relative = Path("tasks") / new_rt_id / "agent-session" / new_sess_id / placement.rest
                session_files[key][placement.rest] = final_dir / relative
            else:
                relative = Path("tasks") / new_rt_id / placement.rest
                task_files[placement.task_folder][placement.rest] = final_dir / relative

            source = extract_root / path
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination)

        for task in valid.tasks:
            primary = task.get("session") or {}
            primary_folder = primary.get("id")
            if primary_folder:
                session_ids.setdefault((task["id"], primary_folder), new_id())

        _cleanup_dir(extract_root)
        (staging / _IMPORT_MARKER).write_text(run_id, encoding="utf-8")

        # 5. Resolve the installed catalog and build every row in one transaction.
        session = db_engine.session_factory()()
        bench = (await session.execute(
            select(Benchmark).where(Benchmark.key == valid.benchmark_key))).scalar_one_or_none()
        if bench is None:
            raise ImportRejected(f"unknown benchmark: {valid.benchmark_key!r}")
        if not bench.enabled:
            raise ImportRejected(f"benchmark is disabled: {valid.benchmark_key!r}")
        tool = (await session.execute(
            select(AgentTool).where(AgentTool.key == valid.agent_tool_key))).scalar_one_or_none()
        if tool is None:
            raise ImportRejected(f"unknown agent tool: {valid.agent_tool_key!r}")
        if not tool.enabled:
            raise ImportRejected(f"agent tool is disabled: {valid.agent_tool_key!r}")
        setup = SETUPS.get(valid.setup_key) or ARCHIVE_SETUPS.get(valid.setup_key)
        if setup is None:
            raise ImportRejected(f"unknown setup: {valid.setup_key!r}")
        supported_setups = bench.manifest.get("setups", list(SETUPS))
        if valid.setup_key not in supported_setups and not setup.archived_only:
            raise ImportRejected(
                f"setup {valid.setup_key!r} is not supported by benchmark "
                f"{valid.benchmark_key!r}"
            )

        task_by_key: dict[str, Task] = {}
        for task in valid.tasks:
            key = task["taskKey"]
            installed = (await session.execute(select(Task).where(
                Task.benchmark_id == bench.id, Task.task_key == key))).scalar_one_or_none()
            if installed is None:
                raise ImportRejected(f"task not installed for benchmark: {key!r}")
            task_by_key[key] = installed

        config = dict(valid.run.get("config") or {})
        import_block: dict[str, Any] = {
            "format": provenance.format,
            "sourceRunId": provenance.source_run_id,
        }
        if provenance.created_at:
            import_block["createdAt"] = provenance.created_at
        config["import"] = import_block

        run = Run(
            id=run_id,
            benchmark_id=bench.id,
            agent_tool_id=tool.id,
            setup_key=valid.setup_key,
            model=valid.run.get("model") or "",
            status=valid.run["status"],
            config=config,
            task_timeout_seconds=valid.run.get("taskTimeoutSeconds")
            or settings.defaults.task_timeout_seconds,
            queued_at=_parse_dt(valid.run.get("queuedAt")) or utcnow(),
            started_at=_parse_dt(valid.run.get("startedAt")),
            finished_at=_parse_dt(valid.run.get("finishedAt")),
            created_at=utcnow(),
        )
        session.add(run)

        for task in valid.tasks:
            folder = task["id"]
            new_rt_id = new_task_ids[folder]
            run_task = RunTask(
                id=new_rt_id,
                run_id=run_id,
                task_id=task_by_key[task["taskKey"]].id,
                ordinal=task["ordinal"],
                status=task["status"],
                timeout_seconds=task.get("timeoutSeconds")
                or settings.defaults.task_timeout_seconds,
                started_at=_parse_dt(task.get("startedAt")),
                finished_at=_parse_dt(task.get("finishedAt")),
            )
            session.add(run_task)

            primary = task.get("session") or {}
            primary_folder = primary.get("id")
            primary_files = session_files.get((folder, primary_folder), {}) if primary_folder else {}

            result = task.get("result")
            if isinstance(result, dict):
                files = task_files.get(folder, {})
                task_dir = final_dir / "tasks" / new_rt_id
                eval_dir = (
                    str(task_dir / "eval")
                    if any(rest.startswith("eval/") for rest in files)
                    else None
                )
                session.add(TaskResult(
                    run_task_id=new_rt_id,
                    passed=bool(result.get("passed")),
                    reason=result.get("reason") or "",
                    duration_seconds=float(result.get("durationSeconds") or 0.0),
                    agent_seconds=float(result.get("agentSeconds") or 0.0),
                    evaluate_seconds=float(result.get("evaluateSeconds") or 0.0),
                    tokens_input=int(result.get("tokensInput") or 0),
                    tokens_output=int(result.get("tokensOutput") or 0),
                    model=result.get("model") or "",
                    metrics=result.get("metrics") or {},
                    details=result.get("details") or {},
                    prompt_path=_as_str(files.get("prompt.md")),
                    response_path=_as_str(files.get("response.md")),
                    diff_path=_as_str(files.get("diff.patch")),
                    terminal_path=_as_str(primary_files.get("terminal.log")),
                    events_path=_as_str(primary_files.get("events.jsonl")),
                    eval_dir=eval_dir,
                ))

            # A session row for every session folder that carries evidence,
            # enriched with summary metadata when the folder is the primary one.
            for (task_folder, session_folder), new_sess_id in session_ids.items():
                if task_folder != folder:
                    continue
                meta = primary if primary_folder == session_folder else {}
                status = meta.get("status") if meta else None
                if status is not None and status not in _TERMINAL_SESSION:
                    raise ImportRejected(f"session status is not importable: {status!r}")
                files = session_files.get((task_folder, session_folder), {})
                session.add(AgentSession(
                    id=new_sess_id,
                    run_task_id=new_rt_id,
                    status=status or "ended",
                    terminal_path=_as_str(files.get("terminal.log")),
                    events_path=_as_str(files.get("events.jsonl")),
                    started_at=_parse_dt(meta.get("startedAt")) or utcnow(),
                    finished_at=_parse_dt(meta.get("finishedAt")),
                ))

        await session.flush()

        # 6. Atomically promote staging, then commit. Order matters: the run
        #    directory must be in place before the rows referencing it commit.
        _rename_staging(staging, final_dir)
        await _commit_import(session)
        try:
            (final_dir / _IMPORT_MARKER).unlink()
        except OSError:
            # A committed row makes a leftover marker safe to reconcile on
            # the next startup; never undo a successful DB commit here.
            pass
        return run_id
    except Exception:
        if session is not None:
            await session.rollback()
        if final_dir is not None and final_dir.exists():
            _cleanup_dir(final_dir)
        if staging is not None:
            _cleanup_dir(staging)
        raise
    finally:
        if session is not None:
            await session.close()


def _as_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None
