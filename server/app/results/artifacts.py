"""Positive evidence catalog and ownership-aware filesystem resolver."""
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import AgentSession, RunTask


_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_STEM = r"[A-Za-z0-9_-]{1,128}"
_EVAL_KEY = re.compile(rf"^eval-log:({_STEM})$")
_SELF_RESULT_KEY = re.compile(r"^self-check:(\d{4}):result$")
_SELF_LOG_KEY = re.compile(rf"^self-check:(\d{{4}}):log:({_STEM})$")
_ATTEMPT_DIR = re.compile(r"^attempt-(\d{4})$")


class ArtifactNotFound(Exception):
    pass


class ArtifactTooLarge(Exception):
    pass


class ArtifactRef(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str
    available: bool
    media_type: str = Field(alias="mediaType")
    size_bytes: int = Field(alias="sizeBytes")
    view_url: str = Field(alias="viewUrl")
    download_url: str = Field(alias="downloadUrl")


@dataclass(frozen=True)
class ArtifactSpec:
    key: str
    relative_path: Path
    media_type: str


@dataclass(frozen=True)
class ResolvedArtifact:
    key: str
    path: Path
    relative_path: Path
    media_type: str
    size_bytes: int
    private_root: Path

    @property
    def filename(self) -> str:
        safe_key = re.sub(r"[^A-Za-z0-9._-]+", "-", self.key).strip("-")
        suffix = self.path.suffix if self.path.suffix else ".txt"
        return f"{safe_key}{suffix}" if not safe_key.endswith(suffix) else safe_key


_TASK_STATIC: tuple[ArtifactSpec, ...] = (
    ArtifactSpec("prompt", Path("prompt.md"), "text/markdown"),
    ArtifactSpec("response", Path("response.md"), "text/markdown"),
    ArtifactSpec("diff", Path("diff.patch"), "text/x-diff"),
    ArtifactSpec("workspace-meta", Path("workspace_meta.json"), "application/json"),
    ArtifactSpec("retrieval-context", Path("retrieval/context.md"), "text/markdown"),
    ArtifactSpec("retrieval-queries", Path("retrieval/queries.json"), "application/json"),
    ArtifactSpec("retrieval-hits", Path("retrieval/hits.json"), "application/json"),
    ArtifactSpec("retrieval-provenance", Path("retrieval/provenance.json"), "application/json"),
    ArtifactSpec("retrieval-invocations", Path("retrieval/invocations.jsonl"), "application/x-ndjson"),
    ArtifactSpec("study-source-table", Path("study/source-table.md"), "text/markdown"),
    ArtifactSpec("study-source-csv", Path("study/source.csv"), "text/csv"),
)
_TASK_BY_KEY = {spec.key: spec for spec in _TASK_STATIC}
_SESSION_STATIC: tuple[ArtifactSpec, ...] = (
    ArtifactSpec("terminal", Path("terminal.log"), "text/plain"),
    ArtifactSpec("transcript", Path("transcript.txt"), "text/plain"),
)


def _component(value: str) -> str:
    if not _SAFE_COMPONENT.fullmatch(value):
        raise ArtifactNotFound("invalid identity")
    return value


def task_root(run_id: str, run_task_id: str) -> Path:
    settings = get_settings()
    return settings.outputs_dir / "runs" / _component(run_id) / "tasks" / _component(run_task_id)


def session_root(run_id: str, run_task_id: str, session_id: str) -> Path:
    return task_root(run_id, run_task_id) / "agent-session" / _component(session_id)


async def owned_task(session: AsyncSession, run_id: str, run_task_id: str) -> RunTask:
    row = (await session.execute(select(RunTask).where(
        RunTask.id == run_task_id,
        RunTask.run_id == run_id,
    ))).scalar_one_or_none()
    if row is None:
        raise ArtifactNotFound("unknown task")
    return row


async def owned_session(
    session: AsyncSession,
    run_id: str,
    run_task_id: str,
    session_id: str,
) -> AgentSession:
    row = (await session.execute(
        select(AgentSession)
        .join(RunTask, AgentSession.run_task_id == RunTask.id)
        .where(
            AgentSession.id == session_id,
            RunTask.id == run_task_id,
            RunTask.run_id == run_id,
        )
    )).scalar_one_or_none()
    if row is None:
        raise ArtifactNotFound("unknown session")
    return row


def _task_spec(key: str) -> ArtifactSpec:
    if key in _TASK_BY_KEY:
        return _TASK_BY_KEY[key]
    if key == "self-check-limit":
        return ArtifactSpec(
            key,
            Path("eval/self-checks/limit-reached.json"),
            "application/json",
        )
    if match := _EVAL_KEY.fullmatch(key):
        return ArtifactSpec(key, Path("eval") / f"{match.group(1)}.log", "text/plain")
    if match := _SELF_RESULT_KEY.fullmatch(key):
        return ArtifactSpec(
            key,
            Path("eval/self-checks") / f"attempt-{match.group(1)}" / "result.json",
            "application/json",
        )
    if match := _SELF_LOG_KEY.fullmatch(key):
        return ArtifactSpec(
            key,
            Path("eval/self-checks") / f"attempt-{match.group(1)}" / "logs" / f"{match.group(2)}.log",
            "text/plain",
        )
    raise ArtifactNotFound("unknown artifact key")


def _under(root: Path, candidate: Path) -> bool:
    return root == candidate or root in candidate.parents


def _inspect(private_root: Path, candidate: Path, key: str, media_type: str) -> ResolvedArtifact:
    settings = get_settings()
    outputs = Path(os.path.abspath(settings.outputs_dir))
    root = Path(os.path.abspath(private_root))
    target = Path(os.path.abspath(candidate))
    if not _under(outputs, root) or not _under(root, target):
        raise ArtifactNotFound("artifact escaped its owner")

    try:
        relative_from_outputs = target.relative_to(outputs)
        relative_from_root = target.relative_to(root)
    except ValueError as exc:
        raise ArtifactNotFound("artifact escaped storage") from exc

    current = outputs
    try:
        if stat.S_ISLNK(os.lstat(current).st_mode):
            raise ArtifactNotFound("symlink storage root")
        for part in relative_from_outputs.parts:
            current = current / part
            mode = os.lstat(current).st_mode
            if stat.S_ISLNK(mode):
                raise ArtifactNotFound("symlink evidence")
    except FileNotFoundError as exc:
        raise ArtifactNotFound("missing artifact") from exc

    try:
        resolved_outputs = outputs.resolve(strict=True)
        resolved_root = root.resolve(strict=True)
        resolved = target.resolve(strict=True)
    except (FileNotFoundError, RuntimeError, OSError) as exc:
        raise ArtifactNotFound("unresolvable artifact") from exc
    if not _under(resolved_outputs, resolved_root) or not _under(resolved_root, resolved):
        raise ArtifactNotFound("resolved artifact escaped its owner")

    mode = os.stat(resolved, follow_symlinks=False).st_mode
    if not stat.S_ISREG(mode) or mode & 0o111:
        raise ArtifactNotFound("evidence is not a non-executable regular file")
    size = os.stat(resolved, follow_symlinks=False).st_size
    return ResolvedArtifact(
        key=key,
        path=resolved,
        relative_path=relative_from_root,
        media_type=media_type,
        size_bytes=size,
        private_root=resolved_root,
    )


def resolve_task_artifact(run_id: str, run_task_id: str, key: str) -> ResolvedArtifact:
    spec = _task_spec(key)
    root = task_root(run_id, run_task_id)
    return _inspect(root, root / spec.relative_path, key, spec.media_type)


def _events_candidate(root: Path, session: AgentSession) -> Path:
    if not session.events_path:
        raise ArtifactNotFound("events unavailable")
    candidate = Path(session.events_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate.name != "events.jsonl":
        raise ArtifactNotFound("unexpected events filename")
    return candidate


def resolve_session_artifact(
    run_id: str,
    run_task_id: str,
    session: AgentSession,
    key: str,
) -> ResolvedArtifact:
    root = session_root(run_id, run_task_id, session.id)
    if key == "events":
        return _inspect(root, _events_candidate(root, session), key, "application/x-ndjson")
    spec = next((item for item in _SESSION_STATIC if item.key == key), None)
    if spec is None:
        raise ArtifactNotFound("unknown session artifact key")
    return _inspect(root, root / spec.relative_path, key, spec.media_type)


def enforce_size(artifact: ResolvedArtifact, *, download: bool) -> None:
    limits = get_settings().evidence
    maximum = limits.download_max_bytes if download else limits.view_max_bytes
    if artifact.size_bytes > maximum:
        raise ArtifactTooLarge(f"artifact exceeds {maximum} bytes")
    if artifact.media_type in {"application/json", "application/x-ndjson"}:
        if artifact.size_bytes > limits.json_max_bytes:
            raise ArtifactTooLarge(f"structured artifact exceeds {limits.json_max_bytes} bytes")


def revalidate(artifact: ResolvedArtifact) -> ResolvedArtifact:
    """Repeat lstat/resolve checks immediately before opening the file."""
    return _inspect(
        artifact.private_root,
        artifact.path,
        artifact.key,
        artifact.media_type,
    )


def _ref(
    spec: ArtifactSpec,
    base_url: str,
    resolver,
) -> ArtifactRef:
    try:
        resolved = resolver()
        available, size = True, resolved.size_bytes
    except ArtifactNotFound:
        available, size = False, 0
    key_url = quote(spec.key, safe=":_-")
    view = f"{base_url}/{key_url}"
    return ArtifactRef(
        key=spec.key,
        available=available,
        mediaType=spec.media_type,
        sizeBytes=size,
        viewUrl=view,
        downloadUrl=f"{view}?download=1",
    )


def _dynamic_task_specs(root: Path) -> list[ArtifactSpec]:
    specs: list[ArtifactSpec] = []
    eval_root = root / "eval"
    try:
        entries = list(eval_root.iterdir())
    except OSError:
        entries = []
    for entry in entries:
        if match := re.fullmatch(rf"({_STEM})\.log", entry.name):
            specs.append(ArtifactSpec(
                f"eval-log:{match.group(1)}", Path("eval") / entry.name, "text/plain",
            ))

    checks = eval_root / "self-checks"
    try:
        attempts = list(checks.iterdir())
    except OSError:
        attempts = []
    for attempt in attempts:
        match = _ATTEMPT_DIR.fullmatch(attempt.name)
        if not match:
            continue
        number = match.group(1)
        specs.append(ArtifactSpec(
            f"self-check:{number}:result",
            Path("eval/self-checks") / attempt.name / "result.json",
            "application/json",
        ))
        logs = attempt / "logs"
        try:
            log_entries = list(logs.iterdir())
        except OSError:
            log_entries = []
        for log in log_entries:
            if log_match := re.fullmatch(rf"({_STEM})\.log", log.name):
                specs.append(ArtifactSpec(
                    f"self-check:{number}:log:{log_match.group(1)}",
                    Path("eval/self-checks") / attempt.name / "logs" / log.name,
                    "text/plain",
                ))
    if (checks / "limit-reached.json").exists():
        specs.append(_task_spec("self-check-limit"))
    return sorted(specs, key=lambda item: item.key)


def task_artifact_refs(run_id: str, run_task_id: str) -> list[ArtifactRef]:
    root = task_root(run_id, run_task_id)
    specs = [*_TASK_STATIC, *_dynamic_task_specs(root)]
    base = f"/api/runs/{quote(run_id)}/tasks/{quote(run_task_id)}/artifacts"
    return [
        _ref(spec, base, lambda spec=spec: resolve_task_artifact(run_id, run_task_id, spec.key))
        for spec in specs
    ]


def session_artifact_refs(
    run_id: str,
    run_task_id: str,
    session: AgentSession,
) -> list[ArtifactRef]:
    specs = [*_SESSION_STATIC, ArtifactSpec("events", Path("events.jsonl"), "application/x-ndjson")]
    base = (
        f"/api/runs/{quote(run_id)}/tasks/{quote(run_task_id)}/sessions/"
        f"{quote(session.id)}/artifacts"
    )
    return [
        _ref(
            spec,
            base,
            lambda spec=spec: resolve_session_artifact(run_id, run_task_id, session, spec.key),
        )
        for spec in specs
    ]


def ref_dicts(refs: list[ArtifactRef]) -> list[dict]:
    return [ref.model_dump(by_alias=True) for ref in refs]