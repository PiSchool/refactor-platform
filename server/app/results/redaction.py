"""Non-destructive secret and private-path redaction for public evidence.

The source artifact is never rewritten. Text is processed with an overlap
window so a credential split across file chunks cannot escape; JSON and JSONL
are parsed and recursively sanitized so their output remains structured.
"""
from __future__ import annotations

import codecs
import json
import os
import re
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any


REDACTED = "[REDACTED]"
PRIVATE_PATH = "[PRIVATE_PATH]"
_MAX_PATTERN_WIDTH = 4096
_MIN_OVERLAP = _MAX_PATTERN_WIDTH * 2
_MIN_SECRET_LENGTH = 8

_PATH_FIELD = re.compile(
    r"(?:path|dir|root|workspacepath|provenancepath|invocationspath)$",
    re.IGNORECASE,
)
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


def _is_absolute_path(value: str) -> bool:
    return value.startswith("/") or bool(_WINDOWS_ABSOLUTE.match(value))


def _configured_provider_key_names() -> set[str]:
    """Key variables of the declared providers, so a provider added purely in
    configuration is redacted as thoroughly as a shipped one."""
    try:
        from app.config import get_settings

        return {p.api_key_env for p in get_settings().providers if p.api_key_env}
    except Exception:
        return set()


def _is_sensitive_key(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", value.lower())
    # Usage telemetry is evidence, not a credential. Keep these fields while
    # still redacting apiToken/accessToken/sessionToken and similar values.
    if normalized.startswith("tokens") or normalized in {
        "totaltokens", "contexttokens", "inputtokens", "outputtokens",
        "reasoningtokens", "cachereadtokens",
    }:
        return False
    if any(part in normalized for part in (
        "authorization", "cookie", "credential", "password", "passwd",
    )):
        return True
    return normalized.endswith((
        "secret", "token", "apikey", "accesskey", "privatekey", "sessionkey",
    ))


class Redactor:
    """One sanitizer shared by API responses, live event replay, and ZIPs."""

    def __init__(
        self,
        secret_values: Sequence[str] = (),
        private_paths: Sequence[str | Path] = (),
    ) -> None:
        self.secret_values = tuple(sorted({
            str(value) for value in secret_values if str(value)
        }, key=len, reverse=True))
        self.private_paths = tuple(sorted({
            str(value) for value in private_paths
            if str(value) not in {"", ".", "/"}
        }, key=len, reverse=True))
        self._patterns: tuple[tuple[re.Pattern[str], str | Any], ...] = (
            (
                re.compile(
                    rf"(?im)(\b(?:authorization|proxy-authorization|cookie|set-cookie)"
                    rf"[ \t]*:[ \t]*)([^\r\n]{{1,{_MAX_PATTERN_WIDTH}}})"
                ),
                rf"\1{REDACTED}",
            ),
            (
                # Any assignment whose variable name reads like a credential.
                # Naming the vendors instead would leak the moment someone
                # configures a provider this list has never heard of.
                re.compile(
                    rf"(?im)(\b[A-Z][A-Z0-9_]*_(?:API_KEY|APIKEY|KEY|TOKEN|SECRET|PASSWORD)"
                    rf"[ \t]*[=:][ \t]*)([^\s\r\n]{{1,{_MAX_PATTERN_WIDTH}}})"
                ),
                rf"\1{REDACTED}",
            ),
            (
                re.compile(
                    rf"(?i)\bBearer[ \t]+[A-Za-z0-9._~+/=-]{{8,{_MAX_PATTERN_WIDTH}}}"
                ),
                f"Bearer {REDACTED}",
            ),
            (
                re.compile(rf"\bsk-or-(?:v1-)?[A-Za-z0-9_-]{{8,{_MAX_PATTERN_WIDTH}}}"),
                REDACTED,
            ),
            (
                re.compile(
                    rf"\b(?:github_pat_[A-Za-z0-9_]|gh[pousr]_[A-Za-z0-9])"
                    rf"[A-Za-z0-9_]{{19,{_MAX_PATTERN_WIDTH}}}"
                ),
                REDACTED,
            ),
            (
                re.compile(r"\b(?:AKIA|ASIA|AIDA|AROA|AIPA|ANPA|ANVA|ASCA)[A-Z0-9]{16}\b"),
                REDACTED,
            ),
        )
        literal_patterns = [re.compile(re.escape(value)) for value in (
            *self.secret_values, *self.private_paths,
        )]
        self._matchers = tuple(literal_patterns) + tuple(pattern for pattern, _ in self._patterns)
        longest_literal = max((len(value) for value in (
            *self.secret_values, *self.private_paths,
        )), default=0)
        self.overlap = max(_MIN_OVERLAP, longest_literal * 2)

    @classmethod
    def from_environment(
        cls,
        private_paths: Sequence[str | Path] = (),
    ) -> "Redactor":
        names = {
            # what the platform hands an agent, whichever provider is active
            "RP_PROVIDER_API_KEY",
            "COPILOT_GITHUB_TOKEN",
            "GITHUB_TOKEN",
            "GH_TOKEN",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "AWS_SECURITY_TOKEN",
        }
        names.update(_configured_provider_key_names())
        for name in os.environ:
            if _is_sensitive_key(name.upper()):
                names.add(name)
        return cls(
            # a very short value would match ordinary text and mangle evidence
            secret_values=[
                value for name in names
                if len(value := os.environ.get(name, "").strip()) >= _MIN_SECRET_LENGTH
            ],
            private_paths=private_paths,
        )

    def redact_text(self, value: str) -> str:
        for secret in self.secret_values:
            value = value.replace(secret, REDACTED)
        for private in self.private_paths:
            value = value.replace(private, PRIVATE_PATH)
        for pattern, replacement in self._patterns:
            value = pattern.sub(replacement, value)
        return value

    def sanitize(self, value: Any, *, drop_path_fields: bool = False) -> Any:
        if isinstance(value, dict):
            clean: dict[str, Any] = {}
            for raw_key, item in value.items():
                key = str(raw_key)
                if _is_sensitive_key(key):
                    clean[key] = REDACTED
                    continue
                if drop_path_fields and _PATH_FIELD.search(key):
                    continue
                if drop_path_fields and isinstance(item, str) and _is_absolute_path(item):
                    continue
                clean[key] = self.sanitize(item, drop_path_fields=drop_path_fields)
            return clean
        if isinstance(value, list):
            return [self.sanitize(item, drop_path_fields=drop_path_fields) for item in value]
        if isinstance(value, tuple):
            return [self.sanitize(item, drop_path_fields=drop_path_fields) for item in value]
        if isinstance(value, str):
            if drop_path_fields and _is_absolute_path(value):
                return PRIVATE_PATH
            return self.redact_text(value)
        return value

    def _safe_cutoff(self, buffer: str, desired: int) -> int:
        cutoff = desired
        for pattern in self._matchers:
            for match in pattern.finditer(buffer):
                if match.start() < cutoff < match.end():
                    cutoff = min(cutoff, match.start())
        return cutoff

    def iter_text(self, path: Path, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        buffer = ""
        with path.open("rb") as handle:
            while chunk := handle.read(max(1, chunk_size)):
                buffer += decoder.decode(chunk)
                if len(buffer) <= self.overlap * 2:
                    continue
                cutoff = self._safe_cutoff(buffer, len(buffer) - self.overlap)
                if cutoff:
                    yield self.redact_text(buffer[:cutoff]).encode("utf-8")
                    buffer = buffer[cutoff:]
            buffer += decoder.decode(b"", final=True)
        if buffer:
            yield self.redact_text(buffer).encode("utf-8")

    def json_bytes(self, path: Path) -> bytes:
        value = json.loads(path.read_text(encoding="utf-8"))
        return (json.dumps(self.sanitize(value), ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    def iter_json_lines(self, path: Path) -> Iterator[bytes]:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    yield (self.redact_text(line.rstrip("\r\n")) + "\n").encode("utf-8")
                    continue
                yield (json.dumps(self.sanitize(value), ensure_ascii=False) + "\n").encode("utf-8")

    def iter_file(self, path: Path, media_type: str, chunk_size: int) -> Iterator[bytes]:
        if media_type == "application/json":
            yield self.json_bytes(path)
        elif media_type == "application/x-ndjson":
            yield from self.iter_json_lines(path)
        else:
            yield from self.iter_text(path, chunk_size=chunk_size)


class IncrementalTextRedactor:
    """Redact complete terminal lines while retaining an unsafe partial tail.

    Credentials and private paths can be split across arbitrary PTY reads. The
    current line is withheld until a newline, or finalization, makes its whole
    content available to the same redactor used by REST evidence responses.
    """

    def __init__(self, redactor: Redactor) -> None:
        self._redactor = redactor
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._buffer = ""
        self._finalized = False

    def feed(self, data: bytes) -> bytes:
        if self._finalized:
            raise RuntimeError("incremental redactor is already finalized")
        self._buffer += self._decoder.decode(data)
        cutoff = self._buffer.rfind("\n") + 1
        if cutoff <= 0:
            return b""
        complete = self._buffer[:cutoff]
        self._buffer = self._buffer[cutoff:]
        return self._redactor.redact_text(complete).encode("utf-8")

    def finalize(self) -> bytes:
        if self._finalized:
            return b""
        self._finalized = True
        self._buffer += self._decoder.decode(b"", final=True)
        output = self._redactor.redact_text(self._buffer).encode("utf-8")
        self._buffer = ""
        return output


def public_data(value: Any, private_paths: Sequence[str | Path] = ()) -> Any:
    """Sanitize API/summary JSON and remove storage implementation fields."""
    return Redactor.from_environment(private_paths).sanitize(value, drop_path_fields=True)