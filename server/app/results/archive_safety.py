"""Archive-safety foundation for untrusted ZIP imports.

The domain API here never loads a whole archive into memory: callers pass a
`Path` to the archive on disk, its central directory is validated member by
member (name, compression, encryption, declared size/ratio, required names)
*before* any bytes are decompressed, and extraction streams each member in
bounded chunks, verifying the actual bytes produced against the declared and
(optionally) externally expected size/hash. Anything this module creates on
disk during a failed extraction is removed before the error propagates.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import IO, Any, Mapping, Sequence

# Defaults (overridable via `RP_IMPORT_*` environment variables; see
# `ImportLimits.from_env`).
DEFAULT_MAX_UPLOAD_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_TOTAL_UNCOMPRESSED_BYTES = 4 * 1024 * 1024 * 1024
DEFAULT_MAX_MEMBERS = 20_000
DEFAULT_MAX_MEMBER_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_PATH_DEPTH = 32
DEFAULT_MAX_COMPONENT_LENGTH = 128
DEFAULT_MAX_PATH_LENGTH = 4096
DEFAULT_MAX_COMPRESSION_RATIO = 200
DEFAULT_MAX_JSON_BYTES = 16 * 1024 * 1024
DEFAULT_CHUNK_BYTES = 64 * 1024
DEFAULT_MAX_JSON_DEPTH = 64

_SUPPORTED_COMPRESSION = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})
_ENCRYPTED_FLAG = 0x1

_ENV_PREFIX = "RP_IMPORT_"
_ENV_FIELDS: tuple[str, ...] = (
    "max_upload_bytes",
    "max_total_uncompressed_bytes",
    "max_members",
    "max_member_bytes",
    "max_path_depth",
    "max_component_length",
    "max_path_length",
    "max_compression_ratio",
    "max_json_bytes",
    "chunk_bytes",
)


class ArchiveSafetyError(Exception):
    """Base for every archive-safety validation/extraction failure."""


class ArchiveTooLarge(ArchiveSafetyError):
    """Declared or actual size/ratio/count exceeds a configured limit."""


class ArchiveMemberInvalid(ArchiveSafetyError):
    """A single member's name or metadata failed validation."""


class ArchiveManifestError(ArchiveSafetyError):
    """Required members are missing (or duplicated) in the archive."""


class ArchiveIntegrityError(ArchiveSafetyError):
    """A member's actual bytes don't match its declared or expected metadata."""


@dataclass(frozen=True)
class ImportLimits:
    """Immutable bounds enforced on every untrusted archive import."""

    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
    max_total_uncompressed_bytes: int = DEFAULT_MAX_TOTAL_UNCOMPRESSED_BYTES
    max_members: int = DEFAULT_MAX_MEMBERS
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES
    max_path_depth: int = DEFAULT_MAX_PATH_DEPTH
    max_component_length: int = DEFAULT_MAX_COMPONENT_LENGTH
    max_path_length: int = DEFAULT_MAX_PATH_LENGTH
    max_compression_ratio: int = DEFAULT_MAX_COMPRESSION_RATIO
    max_json_bytes: int = DEFAULT_MAX_JSON_BYTES
    chunk_bytes: int = DEFAULT_CHUNK_BYTES

    def __post_init__(self) -> None:
        for field_name in _ENV_FIELDS:
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be greater than zero")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "ImportLimits":
        """Build limits from defaults, overridden by `RP_IMPORT_*` variables."""
        source = os.environ if env is None else env
        overrides: dict[str, int] = {}
        for field_name in _ENV_FIELDS:
            raw = source.get(_ENV_PREFIX + field_name.upper())
            if raw is None or not str(raw).strip():
                continue
            overrides[field_name] = int(raw)
        return cls(**overrides)


@dataclass(frozen=True)
class ExpectedMember:
    """Out-of-band size/hash for one member, verified during extraction."""

    size_bytes: int | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class MemberPlan:
    """One member drawn from the central directory, already fully validated."""

    name: str
    relative_path: str
    is_dir: bool
    size_bytes: int
    compress_size: int
    compress_type: int


@dataclass(frozen=True)
class ExtractionPlan:
    """Immutable, fully-validated plan for extracting an archive.

    Built once from the central directory, before any member's bytes are
    read; `extract_plan` replays it to stream and verify each member.
    """

    archive_path: Path
    archive_identity: _ArchiveIdentity
    destination_root: Path
    members: tuple[MemberPlan, ...]
    limits: ImportLimits
    expected: Mapping[str, ExpectedMember]


@dataclass(frozen=True)
class _ArchiveIdentity:
    device: int
    inode: int
    size_bytes: int
    modified_ns: int
    sha256: str


def _identify_archive(handle: IO[bytes], limits: ImportLimits) -> _ArchiveIdentity:
    before = os.fstat(handle.fileno())
    if before.st_size > limits.max_upload_bytes:
        raise ArchiveTooLarge(
            f"archive is {before.st_size} bytes, limit is {limits.max_upload_bytes} bytes"
        )
    handle.seek(0)
    hasher = hashlib.sha256()
    total = 0
    while True:
        chunk = handle.read(limits.chunk_bytes)
        if not chunk:
            break
        total += len(chunk)
        if total > limits.max_upload_bytes:
            raise ArchiveTooLarge(
                f"archive exceeds the {limits.max_upload_bytes}-byte upload limit"
            )
        hasher.update(chunk)
    after = os.fstat(handle.fileno())
    before_key = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_key = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_key != after_key or total != after.st_size:
        raise ArchiveIntegrityError("archive changed while it was being validated")
    handle.seek(0)
    return _ArchiveIdentity(
        device=after.st_dev,
        inode=after.st_ino,
        size_bytes=after.st_size,
        modified_ns=after.st_mtime_ns,
        sha256=hasher.hexdigest(),
    )


def _same_open_archive(handle: IO[bytes], identity: _ArchiveIdentity) -> bool:
    current = os.fstat(handle.fileno())
    return (
        current.st_dev == identity.device
        and current.st_ino == identity.inode
        and current.st_size == identity.size_bytes
        and current.st_mtime_ns == identity.modified_ns
    )


def validate_upload_size(archive_path: Path, limits: ImportLimits) -> None:
    """Reject an archive whose on-disk (compressed) size is too large to
    even open, without reading any of its content."""
    size = os.path.getsize(archive_path)
    if size > limits.max_upload_bytes:
        raise ArchiveTooLarge(
            f"archive is {size} bytes, limit is {limits.max_upload_bytes} bytes"
        )


def _validate_raw_name(name: str, limits: ImportLimits) -> str:
    """Sanitize one member's declared name; return its posix relative path.

    Rejects absolute/drive/backslash/traversal/NUL paths and anything over
    the configured depth/component/total-length limits.
    """
    if not name:
        raise ArchiveMemberInvalid("member name is empty")
    if "\x00" in name:
        raise ArchiveMemberInvalid(f"member name contains a NUL byte: {name!r}")
    if "\\" in name:
        raise ArchiveMemberInvalid(f"member name contains a backslash: {name!r}")
    if name.startswith("/"):
        raise ArchiveMemberInvalid(f"member name is absolute: {name!r}")
    if len(name) >= 2 and name[1] == ":" and name[0].isalpha():
        raise ArchiveMemberInvalid(f"member name has a drive letter: {name!r}")
    if len(name) > limits.max_path_length:
        raise ArchiveMemberInvalid(
            f"member path exceeds {limits.max_path_length} characters: {name!r}"
        )

    parts = name.split("/")
    if parts[-1] == "":
        # Directory entries carry a trailing slash; drop the empty tail part.
        parts = parts[:-1]
    if not parts:
        raise ArchiveMemberInvalid("member name is empty")
    if len(parts) > limits.max_path_depth:
        raise ArchiveMemberInvalid(
            f"member path exceeds depth {limits.max_path_depth}: {name!r}"
        )
    for part in parts:
        if part in ("", ".", ".."):
            raise ArchiveMemberInvalid(f"member path has an unsafe component: {name!r}")
        if len(part) > limits.max_component_length:
            raise ArchiveMemberInvalid(
                f"member path component exceeds {limits.max_component_length} "
                f"characters: {name!r}"
            )
    return "/".join(parts)


def _dedup_key(relative_path: str) -> str:
    """Normalize a path so NFC/casefold-equivalent names collide."""
    return unicodedata.normalize("NFC", relative_path).casefold()


def _reject_encrypted(info: zipfile.ZipInfo) -> None:
    if info.flag_bits & _ENCRYPTED_FLAG:
        raise ArchiveMemberInvalid(f"member is encrypted: {info.filename!r}")


def _reject_unsupported_compression(info: zipfile.ZipInfo) -> None:
    if info.compress_type not in _SUPPORTED_COMPRESSION:
        raise ArchiveMemberInvalid(
            f"member {info.filename!r} uses unsupported compression method "
            f"{info.compress_type}"
        )


def _reject_non_regular(info: zipfile.ZipInfo, *, is_dir: bool) -> None:
    """Reject symlinks and any other non-regular Unix member type.

    Members created on non-Unix systems, or written without ever setting a
    Unix file-type bit (the common case for `ZipFile.writestr`), carry no
    file-type bits in `external_attr` at all — that absence is treated as
    "regular file", not as a violation.
    """
    mode = (info.external_attr >> 16) & 0xFFFF
    file_type = stat.S_IFMT(mode)
    allowed_type = stat.S_IFDIR if is_dir else stat.S_IFREG
    if file_type in (0, allowed_type):
        return
    if stat.S_ISLNK(mode):
        raise ArchiveMemberInvalid(f"member is a symlink: {info.filename!r}")
    raise ArchiveMemberInvalid(f"member is not a regular file: {info.filename!r}")


def build_extraction_plan(
    archive_path: Path,
    destination_root: Path,
    *,
    limits: ImportLimits = ImportLimits(),
    required_names: Sequence[str] = (),
    expected: Mapping[str, ExpectedMember] | None = None,
) -> ExtractionPlan:
    """Validate an archive's central directory and return an immutable plan.

    Every check here reads only central-directory metadata (name, flags,
    compression method, declared sizes) — no member's compressed bytes are
    read. Raises the most specific `ArchiveSafetyError` subclass on the
    first violation found.
    """
    archive_path = Path(archive_path)
    validate_upload_size(archive_path, limits)
    expected = dict(expected or {})

    seen_dedup: dict[str, str] = {}
    members: list[MemberPlan] = []
    found_names: set[str] = set()
    total_uncompressed = 0

    raw = archive_path.open("rb")
    try:
        archive_identity = _identify_archive(raw, limits)
        try:
            zf = zipfile.ZipFile(raw)
        except zipfile.BadZipFile as exc:
            raise ArchiveMemberInvalid(f"not a valid ZIP archive: {exc}") from exc
    except Exception:
        raw.close()
        raise

    with raw, zf:
        infos = zf.infolist()
        if len(infos) > limits.max_members:
            raise ArchiveTooLarge(
                f"archive has {len(infos)} members, limit is {limits.max_members}"
            )

        for info in infos:
            relative = _validate_raw_name(info.filename, limits)
            dedup_key = _dedup_key(relative)
            if dedup_key in seen_dedup:
                raise ArchiveMemberInvalid(
                    f"member {info.filename!r} normalizes to the same path as "
                    f"{seen_dedup[dedup_key]!r}"
                )
            seen_dedup[dedup_key] = info.filename

            _reject_encrypted(info)
            is_dir = info.is_dir()
            _reject_non_regular(info, is_dir=is_dir)

            if not is_dir:
                _reject_unsupported_compression(info)

                if info.file_size > limits.max_member_bytes:
                    raise ArchiveTooLarge(
                        f"member {info.filename!r} declares {info.file_size} bytes, "
                        f"limit is {limits.max_member_bytes} bytes"
                    )
                if info.compress_size == 0:
                    if info.file_size > 0:
                        raise ArchiveTooLarge(
                            f"member {info.filename!r} has an impossible "
                            "compression ratio (zero compressed bytes)"
                        )
                elif info.file_size / info.compress_size > limits.max_compression_ratio:
                    raise ArchiveTooLarge(
                        f"member {info.filename!r} exceeds the compression ratio "
                        f"limit of {limits.max_compression_ratio}:1"
                    )

                total_uncompressed += info.file_size
                if total_uncompressed > limits.max_total_uncompressed_bytes:
                    raise ArchiveTooLarge(
                        "archive declares more than "
                        f"{limits.max_total_uncompressed_bytes} uncompressed bytes in total"
                    )

                found_names.add(relative)
                member_expected = expected.get(relative)
                if member_expected is not None and member_expected.size_bytes is not None:
                    if member_expected.size_bytes != info.file_size:
                        raise ArchiveIntegrityError(
                            f"member {relative!r} declares {info.file_size} bytes, "
                            f"expected {member_expected.size_bytes} bytes"
                        )

            members.append(MemberPlan(
                name=info.filename,
                relative_path=relative,
                is_dir=is_dir,
                size_bytes=info.file_size,
                compress_size=info.compress_size,
                compress_type=info.compress_type,
            ))

    missing = sorted(name for name in required_names if name not in found_names)
    if missing:
        raise ArchiveManifestError(f"archive is missing required members: {missing}")
    missing_expected = sorted(set(expected) - found_names)
    if missing_expected:
        raise ArchiveManifestError(
            f"archive is missing expected members: {missing_expected}"
        )

    return ExtractionPlan(
        archive_path=archive_path,
        archive_identity=archive_identity,
        destination_root=Path(destination_root),
        members=tuple(members),
        limits=limits,
        expected=MappingProxyType(expected),
    )


def _ensure_dir(path: Path, created_dirs: list[Path]) -> None:
    if path.is_symlink():
        raise ArchiveMemberInvalid(f"destination component is a symlink: {path}")
    if path.exists():
        if not path.is_dir():
            raise ArchiveMemberInvalid(f"destination component is not a directory: {path}")
        return
    _ensure_dir(path.parent, created_dirs)
    path.mkdir()
    created_dirs.append(path)


def _safe_join(root: Path, relative_path: str) -> Path:
    destination = root / relative_path
    resolved_root = root.resolve(strict=False)
    resolved_destination = destination.resolve(strict=False)
    if resolved_destination != resolved_root and resolved_root not in resolved_destination.parents:
        raise ArchiveMemberInvalid(f"member escapes destination root: {relative_path!r}")
    return destination


def _extract_member(
    zf: zipfile.ZipFile,
    member: MemberPlan,
    destination: Path,
    limits: ImportLimits,
    expected: ExpectedMember | None,
) -> None:
    hasher = hashlib.sha256()
    total = 0
    created = False
    complete = False
    try:
        with zf.open(member.name) as source, open(destination, "xb") as target:
            created = True
            while True:
                chunk = source.read(limits.chunk_bytes)
                if not chunk:
                    break
                total += len(chunk)
                if total > member.size_bytes:
                    raise ArchiveIntegrityError(
                        f"member {member.relative_path!r} produced more than its "
                        f"declared {member.size_bytes} bytes"
                    )
                hasher.update(chunk)
                target.write(chunk)
        if total != member.size_bytes:
            raise ArchiveIntegrityError(
                f"member {member.relative_path!r} produced {total} bytes, "
                f"declared {member.size_bytes} bytes (truncated or forged size)"
            )
        if expected is not None:
            if expected.size_bytes is not None and expected.size_bytes != total:
                raise ArchiveIntegrityError(
                    f"member {member.relative_path!r} produced {total} bytes, "
                    f"expected {expected.size_bytes} bytes"
                )
            if expected.sha256 is not None:
                digest = hasher.hexdigest()
                if expected.sha256 != digest:
                    raise ArchiveIntegrityError(
                        f"member {member.relative_path!r} checksum mismatch: "
                        f"got {digest}, expected {expected.sha256}"
                    )
        complete = True
    except FileExistsError as exc:
        raise ArchiveMemberInvalid(
            f"extraction target already exists: {member.relative_path!r}"
        ) from exc
    except zipfile.BadZipFile as exc:
        raise ArchiveIntegrityError(
            f"member {member.relative_path!r} failed its integrity check: {exc}"
        ) from exc
    finally:
        if created and not complete:
            try:
                destination.unlink()
            except OSError:
                pass


def extract_plan(plan: ExtractionPlan) -> list[Path]:
    """Stream-extract every member of `plan`, verifying it as it is written.

    On any failure, every file and directory this call created is removed
    before the error propagates; anything that already existed is left
    untouched.
    """
    root = plan.destination_root
    if root.is_symlink():
        raise ArchiveMemberInvalid(f"destination root is a symlink: {root}")
    root_existed = root.exists()
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    if not root_existed:
        root.mkdir(parents=True)
        created_dirs.append(root)

    try:
        with plan.archive_path.open("rb") as raw:
            current_identity = _identify_archive(raw, plan.limits)
            if current_identity != plan.archive_identity:
                raise ArchiveIntegrityError(
                    "archive changed between validation and extraction"
                )
            with zipfile.ZipFile(raw) as zf:
                for member in plan.members:
                    destination = _safe_join(root, member.relative_path)
                    if member.is_dir:
                        _ensure_dir(destination, created_dirs)
                        continue
                    _ensure_dir(destination.parent, created_dirs)
                    _extract_member(
                        zf, member, destination, plan.limits,
                        plan.expected.get(member.relative_path),
                    )
                    created_files.append(destination)
            if not _same_open_archive(raw, plan.archive_identity):
                raise ArchiveIntegrityError("archive changed during extraction")
    except Exception:
        for path in reversed(created_files):
            try:
                path.unlink()
            except OSError:
                pass
        for path in reversed(created_dirs):
            try:
                path.rmdir()
            except OSError:
                pass
        raise
    return created_files


def read_json(source: Path | IO[bytes], *, max_bytes: int, chunk_bytes: int = DEFAULT_CHUNK_BYTES) -> Any:
    """Parse JSON from a path or an already-open binary stream (e.g. a
    `zipfile.ZipFile.open()` handle), reading in bounded chunks so an
    oversized payload never has to be fully buffered to be rejected."""
    if isinstance(source, (str, Path)):
        with open(source, "rb") as fh:
            return _read_json_stream(fh, max_bytes=max_bytes, chunk_bytes=chunk_bytes)
    return _read_json_stream(source, max_bytes=max_bytes, chunk_bytes=chunk_bytes)


def _read_json_stream(fh: IO[bytes], *, max_bytes: int, chunk_bytes: int) -> Any:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = fh.read(chunk_bytes)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ArchiveTooLarge(f"JSON payload exceeds {max_bytes} bytes")
        chunks.append(chunk)
    text = b"".join(chunks).decode("utf-8")
    _validate_json_nesting(text)
    return json.loads(text, object_pairs_hook=_unique_object)


def _validate_json_nesting(text: str, max_depth: int = DEFAULT_MAX_JSON_DEPTH) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > max_depth:
                raise ArchiveManifestError(
                    f"JSON nesting exceeds the maximum depth of {max_depth}"
                )
        elif character in "]}":
            depth -= 1


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ArchiveManifestError(f"JSON object contains duplicate key: {key!r}")
        result[key] = value
    return result
