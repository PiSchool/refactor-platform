"""Tests for the archive-safety foundation (`app.results.archive_safety`).

Limits are kept tiny throughout so oversized-declaration tests stay cheap
(kilobytes, not the real megabyte/gigabyte defaults).
"""
from __future__ import annotations

import hashlib
import os
import stat
import struct
import zipfile
from pathlib import Path

import pytest

from app.results.archive_safety import (
    ArchiveIntegrityError,
    ArchiveManifestError,
    ArchiveMemberInvalid,
    ArchiveSafetyError,
    ArchiveTooLarge,
    ExpectedMember,
    ImportLimits,
    build_extraction_plan,
    extract_plan,
    read_json,
    validate_upload_size,
)

_TINY_LIMITS = ImportLimits(
    max_upload_bytes=64 * 1024,
    max_total_uncompressed_bytes=256 * 1024,
    max_members=8,
    max_member_bytes=32 * 1024,
    max_path_depth=4,
    max_component_length=16,
    max_path_length=64,
    max_compression_ratio=50,
    max_json_bytes=1024,
    chunk_bytes=256,
)


def _write_zip(path: Path, entries: dict[str, bytes], *, compress_type=zipfile.ZIP_STORED) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data, compress_type=compress_type)
    return path


def _write_zip_with_infos(path: Path, entries: list[tuple[zipfile.ZipInfo, bytes]]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for info, data in entries:
            zf.writestr(info, data)
    return path


# Raw central-directory patching helpers, used both for structural fixtures
# above (e.g. forged zero-compressed-size) and the header-patched coverage
# at the bottom of this file: `ZipInfo`/`writestr` always recompute
# size/compress_size/CRC from the real payload and normalize flag_bits, so
# genuinely malicious combinations can only be produced by editing the raw
# central directory record bytes directly.
_CD_SIGNATURE = b"PK\x01\x02"


def _central_directory_offset(data: bytes) -> int:
    offset = data.find(_CD_SIGNATURE)
    assert offset != -1, "fixture must contain exactly one central directory record"
    return offset


def _patch_u16(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 2] = struct.pack("<H", value)


def _patch_u32(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 4] = struct.pack("<I", value)


def _single_member_zip_bytes(name: str, payload: bytes) -> bytes:
    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name, payload, compress_type=zipfile.ZIP_STORED)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Central-directory-only structural rejections (no extraction attempted)
# ---------------------------------------------------------------------------

def test_upload_size_over_limit_rejected_without_opening_archive(tmp_path):
    archive = tmp_path / "big.zip"
    archive.write_bytes(b"0" * (_TINY_LIMITS.max_upload_bytes + 1))
    with pytest.raises(ArchiveTooLarge):
        validate_upload_size(archive, _TINY_LIMITS)


def test_build_plan_rejects_upload_over_limit(tmp_path):
    archive = _write_zip(tmp_path / "a.zip", {"member.txt": b"x" * 10})
    archive.write_bytes(archive.read_bytes() + b"0" * (_TINY_LIMITS.max_upload_bytes + 1))
    with pytest.raises(ArchiveTooLarge):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


@pytest.mark.parametrize("name", [
    "/etc/passwd",
    "C:/windows/system32/evil.txt",
    "C:\\windows\\system32\\evil.txt",
    "..\\evil.txt",
    "a/../../etc/passwd",
    "../escape.txt",
    "a/../../../escape.txt",
])
def test_unsafe_member_names_rejected(tmp_path, name):
    archive = _write_zip(tmp_path / "unsafe.zip", {name: b"payload"})
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_nul_byte_in_member_name_rejected_by_raw_validator(tmp_path):
    from app.results.archive_safety import _validate_raw_name

    with pytest.raises(ArchiveMemberInvalid):
        _validate_raw_name("evil\x00.txt", _TINY_LIMITS)


def test_path_depth_over_limit_rejected(tmp_path):
    name = "/".join(["d"] * (_TINY_LIMITS.max_path_depth + 1)) + "/leaf.txt"
    archive = _write_zip(tmp_path / "deep.zip", {name: b"x"})
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_component_length_over_limit_rejected(tmp_path):
    name = ("c" * (_TINY_LIMITS.max_component_length + 1)) + "/leaf.txt"
    archive = _write_zip(tmp_path / "wide.zip", {name: b"x"})
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_path_length_over_limit_rejected(tmp_path):
    name = "a" * (_TINY_LIMITS.max_path_length + 1)
    archive = _write_zip(tmp_path / "long.zip", {name: b"x"})
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_nfc_casefold_duplicate_names_rejected(tmp_path):
    # "café.txt" as NFC (precomposed é) vs NFD (e + combining acute).
    nfc_name = "cafe\u0301.txt".replace("e\u0301", "\u00e9")
    nfd_name = "cafe\u0301.txt"
    archive = _write_zip(tmp_path / "dup.zip", {})
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(nfc_name, b"one")
        zf.writestr(nfd_name, b"two")
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_case_only_duplicate_names_rejected(tmp_path):
    archive = _write_zip(tmp_path / "dup2.zip", {})
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("File.txt", b"one")
        zf.writestr("file.txt", b"two")
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_symlink_member_rejected(tmp_path):
    archive = tmp_path / "link.zip"
    info = zipfile.ZipInfo("evil-link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    _write_zip_with_infos(archive, [(info, b"/etc/passwd")])
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_symlink_member_with_directory_name_rejected(tmp_path):
    archive = tmp_path / "link-dir.zip"
    info = zipfile.ZipInfo("evil-link/")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    _write_zip_with_infos(archive, [(info, b"")])
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_spoofed_non_unix_symlink_metadata_rejected(tmp_path):
    archive = tmp_path / "spoofed-link.zip"
    info = zipfile.ZipInfo("evil-link")
    info.create_system = 0
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    _write_zip_with_infos(archive, [(info, b"target")])
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_non_regular_unix_member_rejected(tmp_path):
    archive = tmp_path / "fifo.zip"
    info = zipfile.ZipInfo("evil-fifo")
    info.create_system = 3
    info.external_attr = (stat.S_IFIFO | 0o644) << 16
    _write_zip_with_infos(archive, [(info, b"")])
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_member_over_max_member_bytes_rejected(tmp_path):
    archive = _write_zip(
        tmp_path / "huge-member.zip",
        {"member.bin": b"x" * (_TINY_LIMITS.max_member_bytes + 1)},
    )
    with pytest.raises(ArchiveTooLarge):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_declared_total_uncompressed_over_limit_rejected(tmp_path):
    per_member = _TINY_LIMITS.max_total_uncompressed_bytes // 3 + 10
    archive = _write_zip(tmp_path / "total.zip", {
        "a.bin": b"x" * per_member,
        "b.bin": b"y" * per_member,
        "c.bin": b"z" * per_member,
    })
    with pytest.raises(ArchiveTooLarge):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_member_count_over_limit_rejected(tmp_path):
    entries = {f"file-{i}.txt": b"x" for i in range(_TINY_LIMITS.max_members + 1)}
    archive = _write_zip(tmp_path / "many.zip", entries)
    with pytest.raises(ArchiveTooLarge):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_compression_ratio_over_limit_rejected(tmp_path):
    # Highly compressible payload, forced to store with a manually inflated
    # declared ratio via many repeated bytes compressed with deflate.
    payload = b"a" * (_TINY_LIMITS.max_component_length * 4000)
    archive = _write_zip(
        tmp_path / "bomb.zip", {"bomb.bin": payload}, compress_type=zipfile.ZIP_DEFLATED,
    )
    with zipfile.ZipFile(archive) as zf:
        info = zf.getinfo("bomb.bin")
        ratio = info.file_size / max(info.compress_size, 1)
    assert ratio > _TINY_LIMITS.max_compression_ratio, "fixture must exceed the tiny ratio limit"
    with pytest.raises(ArchiveTooLarge):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_zero_compressed_size_with_nonzero_declared_size_rejected(tmp_path):
    # `ZipInfo`/`writestr` always recompute size/compress_size from the real
    # payload, so this impossible combination (declared uncompressed bytes
    # with zero compressed bytes) is forged directly in the raw central
    # directory record, the way a hand-crafted malicious archive would.
    raw = bytearray(_single_member_zip_bytes("weird.bin", b"xxxxx"))
    cd = _central_directory_offset(bytes(raw))
    _patch_u32(raw, cd + 20, 0)  # compressed size -> 0
    archive = tmp_path / "zero-compressed.zip"
    archive.write_bytes(bytes(raw))
    with pytest.raises(ArchiveTooLarge):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_required_names_missing_rejected(tmp_path):
    archive = _write_zip(tmp_path / "no-manifest.zip", {"summary.json": b"{}"})
    with pytest.raises(ArchiveManifestError):
        build_extraction_plan(
            archive, tmp_path / "dest", limits=_TINY_LIMITS,
            required_names=("manifest.json", "summary.json"),
        )


def test_required_names_all_present_accepted(tmp_path):
    archive = _write_zip(tmp_path / "manifest.zip", {
        "manifest.json": b"{}", "summary.json": b"{}",
    })
    plan = build_extraction_plan(
        archive, tmp_path / "dest", limits=_TINY_LIMITS,
        required_names=("manifest.json", "summary.json"),
    )
    assert {m.relative_path for m in plan.members} == {"manifest.json", "summary.json"}


def test_expected_size_mismatch_rejected_at_plan_time(tmp_path):
    archive = _write_zip(tmp_path / "expected.zip", {"data.bin": b"x" * 20})
    with pytest.raises(ArchiveIntegrityError):
        build_extraction_plan(
            archive, tmp_path / "dest", limits=_TINY_LIMITS,
            expected={"data.bin": ExpectedMember(size_bytes=999)},
        )


def test_missing_expected_member_rejected_at_plan_time(tmp_path):
    archive = _write_zip(tmp_path / "missing-expected.zip", {"data.bin": b"x"})
    with pytest.raises(ArchiveManifestError):
        build_extraction_plan(
            archive, tmp_path / "dest", limits=_TINY_LIMITS,
            expected={"absent.bin": ExpectedMember(size_bytes=1)},
        )


def test_not_a_zip_file_rejected(tmp_path):
    archive = tmp_path / "not-a-zip.zip"
    archive.write_bytes(b"this is not a zip archive at all")
    with pytest.raises(ArchiveSafetyError):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_error_hierarchy_shares_common_base():
    assert issubclass(ArchiveTooLarge, ArchiveSafetyError)
    assert issubclass(ArchiveMemberInvalid, ArchiveSafetyError)
    assert issubclass(ArchiveManifestError, ArchiveSafetyError)
    assert issubclass(ArchiveIntegrityError, ArchiveSafetyError)


def test_limits_are_immutable():
    with pytest.raises(Exception):
        _TINY_LIMITS.max_upload_bytes = 1


# ---------------------------------------------------------------------------
# Successful extraction
# ---------------------------------------------------------------------------

def test_extract_plan_writes_files_and_directories(tmp_path):
    archive = _write_zip(tmp_path / "good.zip", {
        "manifest.json": b'{"ok": true}',
        "nested/dir/file.txt": b"hello world",
    })
    dest = tmp_path / "dest"
    plan = build_extraction_plan(archive, dest, limits=_TINY_LIMITS)
    created = extract_plan(plan)

    assert (dest / "manifest.json").read_bytes() == b'{"ok": true}'
    assert (dest / "nested" / "dir" / "file.txt").read_bytes() == b"hello world"
    assert set(created) == {dest / "manifest.json", dest / "nested" / "dir" / "file.txt"}


def test_extract_plan_verifies_expected_size_and_hash(tmp_path):
    data = b"expected content"
    archive = _write_zip(tmp_path / "verified.zip", {"data.bin": data})
    dest = tmp_path / "dest"
    plan = build_extraction_plan(
        archive, dest, limits=_TINY_LIMITS,
        expected={"data.bin": ExpectedMember(size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())},
    )
    extract_plan(plan)
    assert (dest / "data.bin").read_bytes() == data


def test_extract_plan_rejects_expected_hash_mismatch_and_cleans_up(tmp_path):
    data = b"expected content"
    archive = _write_zip(tmp_path / "bad-hash.zip", {"data.bin": data})
    dest = tmp_path / "dest"
    plan = build_extraction_plan(
        archive, dest, limits=_TINY_LIMITS,
        expected={"data.bin": ExpectedMember(sha256="0" * 64)},
    )
    with pytest.raises(ArchiveIntegrityError):
        extract_plan(plan)
    assert not (dest / "data.bin").exists()


def test_extract_plan_rejects_destination_escape(tmp_path):
    archive = _write_zip(tmp_path / "escape.zip", {"safe.txt": b"ok"})
    dest = tmp_path / "dest"
    plan = build_extraction_plan(archive, dest, limits=_TINY_LIMITS)
    # Forge a plan member that tries to escape the destination root; this
    # exercises `extract_plan`'s own containment check independent of the
    # (already-passed) central-directory validation.
    from app.results.archive_safety import ExtractionPlan, MemberPlan
    forged = ExtractionPlan(
        archive_path=plan.archive_path,
        archive_identity=plan.archive_identity,
        destination_root=plan.destination_root,
        members=(MemberPlan(
            name="safe.txt", relative_path="../outside.txt",
            is_dir=False, size_bytes=2, compress_size=2, compress_type=zipfile.ZIP_STORED,
        ),),
        limits=plan.limits,
        expected=plan.expected,
    )
    with pytest.raises(ArchiveMemberInvalid):
        extract_plan(forged)
    assert not (tmp_path / "outside.txt").exists()


def test_extract_plan_removes_only_what_it_created_on_failure(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "preexisting.txt").write_text("keep me")

    archive = _write_zip(tmp_path / "partial.zip", {
        "ok.txt": b"fine",
        "data.bin": b"expected content",
    })
    plan = build_extraction_plan(
        archive, dest, limits=_TINY_LIMITS,
        expected={"data.bin": ExpectedMember(sha256="0" * 64)},
    )
    with pytest.raises(ArchiveIntegrityError):
        extract_plan(plan)

    assert (dest / "preexisting.txt").exists()
    assert not (dest / "ok.txt").exists()
    assert not (dest / "data.bin").exists()
    assert dest.exists()  # pre-existing destination root itself is kept


def test_extract_plan_never_overwrites_preexisting_target(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()
    existing = dest / "data.bin"
    existing.write_bytes(b"keep me")
    archive = _write_zip(tmp_path / "collision.zip", {"data.bin": b"replacement"})
    plan = build_extraction_plan(archive, dest, limits=_TINY_LIMITS)

    with pytest.raises(ArchiveSafetyError):
        extract_plan(plan)

    assert existing.read_bytes() == b"keep me"


def test_extract_plan_is_bound_to_archive_bytes_validated_at_plan_time(tmp_path):
    archive = _write_zip(tmp_path / "replace.zip", {"data.bin": b"first"})
    plan = build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)
    replacement = _write_zip(tmp_path / "replacement.zip", {"data.bin": b"other"})
    os.replace(replacement, archive)

    with pytest.raises(ArchiveIntegrityError, match="changed"):
        extract_plan(plan)

    assert not (tmp_path / "dest" / "data.bin").exists()


def test_extract_plan_rejects_symlinked_destination_component(tmp_path):
    archive = _write_zip(tmp_path / "symlink-dest.zip", {"nested/data.bin": b"secret"})
    destination = tmp_path / "dest"
    destination.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, destination / "nested")

    plan = build_extraction_plan(archive, destination, limits=_TINY_LIMITS)
    with pytest.raises(ArchiveMemberInvalid):
        extract_plan(plan)

    assert not (outside / "data.bin").exists()


# ---------------------------------------------------------------------------
# read_json
# ---------------------------------------------------------------------------

def test_read_json_within_limit_parses(tmp_path):
    path = tmp_path / "small.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    assert read_json(path, max_bytes=_TINY_LIMITS.max_json_bytes) == {"a": 1}


def test_read_json_over_limit_rejected(tmp_path):
    path = tmp_path / "large.json"
    path.write_text(("{\"a\": \"" + ("x" * 2000) + "\"}"), encoding="utf-8")
    with pytest.raises(ArchiveTooLarge):
        read_json(path, max_bytes=_TINY_LIMITS.max_json_bytes)


def test_read_json_from_open_zip_member(tmp_path):
    archive = _write_zip(tmp_path / "manifest-only.zip", {"manifest.json": b'{"version": 2}'})
    with zipfile.ZipFile(archive) as zf, zf.open("manifest.json") as fh:
        assert read_json(fh, max_bytes=_TINY_LIMITS.max_json_bytes) == {"version": 2}


def test_read_json_rejects_duplicate_object_keys(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"version": 1, "version": 2}', encoding="utf-8")
    with pytest.raises(ArchiveManifestError):
        read_json(path, max_bytes=_TINY_LIMITS.max_json_bytes)


def test_read_json_rejects_excessive_nesting(tmp_path):
    path = tmp_path / "deep.json"
    path.write_text("[" * 80 + "0" + "]" * 80, encoding="utf-8")
    with pytest.raises(ArchiveManifestError, match="nesting"):
        read_json(path, max_bytes=_TINY_LIMITS.max_json_bytes)


# ---------------------------------------------------------------------------
# Environment overrides
# ---------------------------------------------------------------------------

def test_import_limits_defaults_match_documented_values():
    limits = ImportLimits()
    assert limits.max_upload_bytes == 512 * 1024 * 1024
    assert limits.max_total_uncompressed_bytes == 4 * 1024 * 1024 * 1024
    assert limits.max_members == 20_000
    assert limits.max_member_bytes == 512 * 1024 * 1024
    assert limits.max_path_depth == 32
    assert limits.max_component_length == 128
    assert limits.max_path_length == 4096
    assert limits.max_compression_ratio == 200
    assert limits.max_json_bytes == 16 * 1024 * 1024
    assert limits.chunk_bytes == 64 * 1024


def test_import_limits_from_env_overrides_all_fields():
    env = {
        "RP_IMPORT_MAX_UPLOAD_BYTES": "1",
        "RP_IMPORT_MAX_TOTAL_UNCOMPRESSED_BYTES": "2",
        "RP_IMPORT_MAX_MEMBERS": "3",
        "RP_IMPORT_MAX_MEMBER_BYTES": "4",
        "RP_IMPORT_MAX_PATH_DEPTH": "5",
        "RP_IMPORT_MAX_COMPONENT_LENGTH": "6",
        "RP_IMPORT_MAX_PATH_LENGTH": "7",
        "RP_IMPORT_MAX_COMPRESSION_RATIO": "8",
        "RP_IMPORT_MAX_JSON_BYTES": "9",
        "RP_IMPORT_CHUNK_BYTES": "10",
    }
    limits = ImportLimits.from_env(env)
    assert limits == ImportLimits(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)


def test_import_limits_from_env_ignores_blank_and_missing(monkeypatch):
    limits = ImportLimits.from_env({"RP_IMPORT_MAX_UPLOAD_BYTES": "  "})
    assert limits == ImportLimits()


@pytest.mark.parametrize("field", [
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
])
def test_import_limits_reject_non_positive_values(field):
    values = {item: 1 for item in ImportLimits.__dataclass_fields__}
    values[field] = 0
    with pytest.raises(ValueError, match=field):
        ImportLimits(**values)


# ---------------------------------------------------------------------------
# Raw, header-patched coverage (encryption / unsupported compression / CRC /
# forged size) — these bypass the ZipInfo API (which silently normalizes
# such fields on write) by editing the central-directory record's raw bytes
# directly, the way a hand-crafted malicious archive would.
# ---------------------------------------------------------------------------

def test_header_patched_encryption_flag_rejected(tmp_path):
    raw = bytearray(_single_member_zip_bytes("member.bin", b"hello world!"))
    cd = _central_directory_offset(bytes(raw))
    _patch_u16(raw, cd + 8, 0x1)  # general purpose bit flag: set the encrypted bit

    archive = tmp_path / "encrypted.zip"
    archive.write_bytes(bytes(raw))
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_header_patched_unsupported_compression_rejected(tmp_path):
    raw = bytearray(_single_member_zip_bytes("member.bin", b"hello world!"))
    cd = _central_directory_offset(bytes(raw))
    _patch_u16(raw, cd + 10, 99)  # compression method: not stored/deflated

    archive = tmp_path / "unsupported.zip"
    archive.write_bytes(bytes(raw))
    with pytest.raises(ArchiveMemberInvalid):
        build_extraction_plan(archive, tmp_path / "dest", limits=_TINY_LIMITS)


def test_header_patched_forged_crc_detected_during_extraction(tmp_path):
    payload = b"hello world!"
    raw = bytearray(_single_member_zip_bytes("member.bin", payload))
    cd = _central_directory_offset(bytes(raw))
    real_crc = struct.unpack_from("<I", raw, cd + 16)[0]
    _patch_u32(raw, cd + 16, (real_crc ^ 0xFFFFFFFF) & 0xFFFFFFFF)  # corrupt CRC-32

    archive = tmp_path / "bad-crc.zip"
    archive.write_bytes(bytes(raw))
    dest = tmp_path / "dest"
    plan = build_extraction_plan(archive, dest, limits=_TINY_LIMITS)
    with pytest.raises(ArchiveIntegrityError):
        extract_plan(plan)
    assert not (dest / "member.bin").exists()


def test_header_patched_forged_size_detected_during_extraction(tmp_path):
    payload = b"hello world!"
    raw = bytearray(_single_member_zip_bytes("member.bin", payload))
    cd = _central_directory_offset(bytes(raw))
    _patch_u32(raw, cd + 24, len(payload) + 500)  # inflate the declared uncompressed size

    archive = tmp_path / "forged-size.zip"
    archive.write_bytes(bytes(raw))
    dest = tmp_path / "dest"
    plan = build_extraction_plan(archive, dest, limits=_TINY_LIMITS)
    with pytest.raises(ArchiveIntegrityError):
        extract_plan(plan)
    assert not (dest / "member.bin").exists()
