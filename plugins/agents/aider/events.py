"""Aider's terminal report translated into the platform's event vocabulary.

Aider (0.86.2) has no machine-readable event stream: what it knows about a
session it prints. The lines it prints are a stable part of its interface —
`Aider vX`, `Model: M with F edit format`, `Added P to the chat.`,
`Applied edit to P`, `Tokens: N sent, M received.` — and this module turns them
into the same events the dashboard reads from every other adapter.

Token counts come from that report, so they carry the precision aider prints
(it humanizes above a thousand: `1.2k` is recorded as 1200).

Stdlib only: imported by the adapter and by the wrapper process.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
RE_VERSION = re.compile(r"^Aider v(?P<version>[\w.]+)")
RE_MODEL = re.compile(r"^Model:\s+(?P<model>\S+)\s+with\s+(?P<format>.+?)\s+edit format")
RE_ADDED = re.compile(r"^Added (?P<path>.+) to the chat\.?$")
RE_TOKENS = re.compile(
    r"^Tokens:\s+(?P<sent>[\d.,]+[kKmM]?)\s+sent,\s+(?P<received>[\d.,]+[kKmM]?)\s+received")
RE_APPLIED = re.compile(r"^Applied edit to (?P<path>.+?)\.?$")
RE_FAILED_EDIT = re.compile(r"^(?:Failed to apply edit to|Skipped edit to) (?P<path>.+?)\.?$")
RE_RUNNING = re.compile(r"^Running (?P<command>.+)$")
RE_COMMIT = re.compile(r"^Commit (?P<sha>\w+) ")
# Aider reports provider failures as plain lines among its output. They are
# diagnostics, not the assistant speaking, and the run's flags depend on them.
RE_FAILURE = re.compile(
    r"^(litellm\.|Traceback|\w*Error\b|Rate limit|Connection error|API error|Unexpected error)")
# A retry abandons the reply in progress: what follows is a fresh attempt at the
# same request, so the two must not be shown as one turn.
RE_RETRY = re.compile(r"^Retrying in [\d.]+ seconds?\b")
# Aider's own report when the model exhausts its context. It ends the round trip
# and is followed by the counts it managed to measure.
RE_TOKEN_LIMIT = re.compile(r"^Model .+ has hit a token limit!")
RE_APPROX_TOKENS = re.compile(
    r"^(?P<which>Input|Output) tokens:\s*~?(?P<count>[\d.,]+[kKmM]?)")
# Aider streams the reply without a trailing newline, so a diagnostic can be
# glued to the tail of the assistant's last partial line. Anchored matching then
# reads the diagnostic as the assistant speaking, which loses the run's flags.
RE_GLUED = re.compile(
    r"^(?P<head>.+?)(?P<tail>litellm\.[A-Za-z]*Error\b.*|Model \S+ has hit a token limit!.*)$")

# A model that loops prints the same block over and over. Fold it into one copy
# plus its count: every copy makes the step unreadable and buries the rest of the
# answer. Three occurrences is a loop; two is a coincidence.
MIN_REPEATS = 2
MAX_PERIOD = 8

_NOISE = (
    # The wrapper marks its own lines; they are not the assistant speaking.
    "[aider] ",
    "Detected dumb terminal",
    "Warning: Input is not a terminal",
    "Update git name with:",
    "Update git email with:",
    "https://aider.chat/HISTORY.html",
    "Repo-map:",
    "Git repo:",
)


def humanized(text: str) -> int:
    """`1.2k` -> 1200, `1,234` -> 1234, `56` -> 56."""
    raw = text.strip().replace(",", "")
    multiplier = 1
    if raw[-1:].lower() == "k":
        multiplier, raw = 1000, raw[:-1]
    elif raw[-1:].lower() == "m":
        multiplier, raw = 1000000, raw[:-1]
    try:
        return int(round(float(raw) * multiplier))
    except ValueError:
        return 0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _cycle(lines: list[str], start: int) -> tuple[int, int]:
    """The shortest block repeating at `start`, and how many extra copies follow.

    A looping model rarely repeats a single line: the observed shape is a pair,
    a tool call and a marker, printed over and over. The shortest period is
    preferred so a genuinely repeated line still folds as one line.
    """
    for period in range(1, MAX_PERIOD + 1):
        if start + period > len(lines):
            break
        block = lines[start:start + period]
        repeats, index = 0, start + period
        while lines[index:index + period] == block:
            repeats += 1
            index += period
        if repeats >= MIN_REPEATS:
            return period, repeats
    return 1, 0


def collapsed(lines: list[str]) -> list[str]:
    """A repeating block folded into one copy plus its count.

    Blank runs collapse to a single blank line. Nothing else is altered, and the
    verbatim output remains in the session's terminal log.
    """
    out: list[str] = []
    index = 0
    while index < len(lines):
        period, repeats = _cycle(lines, index)
        block = lines[index:index + period]
        out.extend(block)
        if repeats and period == 1 and not block[0].strip():
            pass                                   # one blank stands for the run
        elif repeats and period == 1:
            out.append(f"[the previous line repeated {repeats} more times]")
        elif repeats:
            out.append(f"[the previous {period} lines repeated {repeats} more times]")
        index += period * (repeats + 1)
    return out


class Translator:
    """One aider stdout line in, platform events out.

    A UI turn spans the assistant's answer up to the token report aider prints
    when a round trip ends.
    """

    def __init__(self, model: str) -> None:
        self.model = model
        self.version = ""
        self.edit_format = ""
        self.turn = -1
        self.turn_open = False
        self.tokens_input = 0
        self.tokens_output = 0
        self.context_tokens = 0
        # What aider measured when a round trip died on the model's context
        # limit, used only when no exact report ever arrived.
        self.approx_input = 0
        self.approx_output = 0
        self.limit_hit = False
        self.retries = 0
        self.round_trips = 0
        self.edits: list[str] = []
        self.failed_edits: list[str] = []
        self.commands: list[str] = []
        self.errors: list[str] = []
        self.files_added: list[str] = []
        self._buffer: list[str] = []
        self._call = 0

    def _event(self, type_: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"type": type_, "timestamp": now_iso(), "data": data}

    def _open_turn(self) -> Iterator[dict[str, Any]]:
        if self.turn_open:
            return
        self.turn += 1
        self.turn_open = True
        yield self._event("assistant.turn_start", {"turnId": str(self.turn)})

    def _flush_message(self) -> Iterator[dict[str, Any]]:
        text = "\n".join(collapsed(self._buffer)).strip()
        self._buffer.clear()
        if not text:
            return
        yield from self._open_turn()
        yield self._event("assistant.message",
                          {"turnId": str(self.turn), "content": text, "outputTokens": 0})

    def _close_turn(self) -> Iterator[dict[str, Any]]:
        yield from self._flush_message()
        if self.turn_open:
            self.turn_open = False
            yield self._event("assistant.turn_end", {"turnId": str(self.turn)})

    def _tool(self, name: str, arguments: dict[str, Any], ok: bool,
              output: str = "") -> Iterator[dict[str, Any]]:
        self._call += 1
        call_id = f"call_{self._call}"
        yield from self._open_turn()
        yield self._event("tool.execution_start", {
            "turnId": str(self.turn), "toolCallId": call_id,
            "toolName": name, "arguments": arguments,
        })
        yield self._event("tool.execution_complete", {
            "turnId": str(self.turn), "toolCallId": call_id,
            "success": ok, "result": {"content": output[:2000]},
        })

    def start(self) -> dict[str, Any]:
        return self._event("session.start", {
            "producer": "aider", "selectedModel": self.model, "version": self.version,
        })

    def prompt(self, text: str) -> dict[str, Any]:
        return self._event("user.message", {"content": text[:4000]})

    def feed(self, raw_line: str) -> Iterator[dict[str, Any]]:
        line = ANSI.sub("", raw_line).rstrip()
        stripped = line.strip()
        if not stripped:
            self._buffer.append("")
            return

        match = RE_VERSION.match(stripped)
        if match:
            self.version = match.group("version")
            yield self._event("system.message", {"content": stripped})
            return
        match = RE_MODEL.match(stripped)
        if match:
            self.model = match.group("model")
            self.edit_format = match.group("format")
            yield self._event("system.message", {"content": stripped})
            return
        match = RE_ADDED.match(stripped)
        if match:
            self.files_added.append(match.group("path"))
            yield self._event("system.message", {"content": stripped})
            return
        match = RE_TOKENS.match(stripped)
        if match:
            self.round_trips += 1
            sent = humanized(match.group("sent"))
            self.tokens_input += sent
            self.tokens_output += humanized(match.group("received"))
            # the last request is what currently occupies the model's window
            self.context_tokens = sent
            yield from self._close_turn()
            return
        match = RE_APPLIED.match(stripped)
        if match:
            path = match.group("path")
            self.edits.append(path)
            yield from self._tool("edit", {"path": path}, True)
            return
        match = RE_FAILED_EDIT.match(stripped)
        if match:
            path = match.group("path")
            self.failed_edits.append(path)
            yield from self._tool("edit", {"path": path}, False, stripped)
            return
        match = RE_RUNNING.match(stripped)
        if match:
            command = match.group("command")
            self.commands.append(command)
            yield from self._tool("shell", {"command": command}, True)
            return
        if RE_COMMIT.match(stripped) or any(stripped.startswith(n) for n in _NOISE):
            yield self._event("system.message", {"content": stripped})
            return
        if RE_FAILURE.match(stripped):
            self.errors.append(stripped)
            yield self._event("system.message", {"content": stripped})
            return
        if RE_RETRY.match(stripped):
            self.retries += 1
            yield from self._close_turn()
            yield self._event("system.message", {"content": stripped})
            return
        if RE_TOKEN_LIMIT.match(stripped):
            self.limit_hit = True
            self.errors.append(stripped)
            yield from self._close_turn()
            yield self._event("system.message", {"content": stripped})
            return
        match = RE_APPROX_TOKENS.match(stripped)
        if match:
            count = humanized(match.group("count"))
            if match.group("which") == "Input":
                self.approx_input = max(self.approx_input, count)
            else:
                self.approx_output = max(self.approx_output, count)
            yield self._event("system.message", {"content": stripped})
            return
        if self.limit_hit:
            # everything after the limit is aider's report and its advice
            yield self._event("system.message", {"content": stripped})
            return
        match = RE_GLUED.match(stripped)
        if match:
            self._buffer.append(match.group("head"))
            yield from self.feed(match.group("tail"))
            return
        self._buffer.append(line)

    def shutdown(self, shutdown_type: str) -> Iterator[dict[str, Any]]:
        # Every answer aider completes ends with its token report, so whatever is
        # still buffered at exit was printed outside a round trip: shutdown
        # diagnostics such as a failed history summarization. Recording it as the
        # assistant's reply would overwrite the answer in the saved response.
        # Nothing completed means aider stopped mid-answer, which is worth keeping.
        if self.round_trips:
            trailing = "\n".join(self._buffer).strip()
            self._buffer.clear()
            if trailing:
                self.errors.append(trailing)
                yield self._event("system.message", {"content": trailing})
        yield from self._close_turn()
        # A round trip that died on the context limit prints no exact report, so
        # the counts aider measured for it are all there is.
        tokens_input = self.tokens_input or self.approx_input
        tokens_output = self.tokens_output or self.approx_output
        yield self._event("session.shutdown", {
            "shutdownType": shutdown_type,
            "currentTokens": self.context_tokens or self.approx_input,
            "editFormat": self.edit_format,
            "filesEdited": sorted(set(self.edits)),
            # how many requests the model answered, and how often aider had to
            # ask again: a retried error that was followed by an answer was
            # transient, and must not be reported as the run's failure
            "roundTrips": self.round_trips,
            "retries": self.retries,
            "modelMetrics": {self.model or "model": {"usage": {
                "inputTokens": tokens_input,
                "outputTokens": tokens_output,
                "cacheReadTokens": 0,
                "reasoningTokens": 0,
            }}},
        })


_AUTH = ("authenticationerror", "401", "invalid api key", "no api key")
_RATE = ("ratelimiterror", "429", "rate limit", "quota")
_TRANSPORT = ("apiconnectionerror", "connection error", "timed out", "econnrefused")
# The model ran out of room. The provider was reachable and the credentials
# worked, so this is neither a transport nor an auth failure, and the empty
# workspace it leaves behind is a symptom rather than the cause.
_CONTEXT = ("has hit a token limit", "contextwindowexceedederror",
            "context window", "prompt is too long")


def parse(events_path: Path | None, terminal_log_path: Path, requested_model: str):
    """Read the normalized file back into the platform's SessionInfo shape."""
    info = {
        "tokens_input": 0, "tokens_output": 0, "tokens_cache_read": 0,
        "tokens_reasoning": 0, "context_tokens": 0, "model": requested_model,
        "response_text": "", "readable_transcript": "", "flags": set(),
        "eval_tool_invocations": 0, "retrieval_invocations": 0,
    }
    rows: list[dict[str, Any]] = []
    if events_path and events_path.is_file():
        for raw in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(raw))
            except ValueError:
                continue
    lines: list[str] = []
    errors: list[str] = []
    round_trips = 0
    for row in rows:
        kind = str(row.get("type", ""))
        data = row.get("data") or {}
        if kind == "session.start":
            info["model"] = str(data.get("selectedModel") or requested_model)
        elif kind == "system.message":
            content = str(data.get("content") or "")
            match = RE_MODEL.match(content)
            if match:
                # aider reports the litellm route (`openai/<model>`); the run
                # records the model the operator selected.
                info["model"] = match.group("model").split("openai/", 1)[-1]
            errors.append(content)
        elif kind == "assistant.message":
            content = str(data.get("content") or "")
            if content:
                info["response_text"] = content
                lines.append(content)
        elif kind == "tool.execution_start":
            name = str(data.get("toolName") or "")
            args = data.get("arguments") or {}
            lines.append(f"→ {name}({json.dumps(args)[:300]})")
            if name == "shell" and "eval.sh" in json.dumps(args):
                info["eval_tool_invocations"] += 1
        elif kind == "session.shutdown":
            info["context_tokens"] = int(data.get("currentTokens") or 0)
            round_trips = int(data.get("roundTrips") or 0)
            for usage in (data.get("modelMetrics") or {}).values():
                u = usage.get("usage") or {}
                info["tokens_input"] += int(u.get("inputTokens") or 0)
                info["tokens_output"] += int(u.get("outputTokens") or 0)

    haystack = " ".join(errors).lower()
    if not rows and terminal_log_path.is_file():
        haystack += " " + terminal_log_path.read_text(encoding="utf-8", errors="replace")[-8000:].lower()
    if any(token in haystack for token in _AUTH):
        info["flags"].add("auth_wall")
    if any(token in haystack for token in _RATE):
        info["flags"].add("rate_limited")
    if any(token in haystack for token in _TRANSPORT) and not round_trips:
        # aider retries a lost connection; one the model answered after is not
        # this run's verdict, and it stays visible in the session's messages
        info["flags"].add("transport_error")
    if any(token in haystack for token in _CONTEXT):
        info["flags"].add("context_limit")
    info["readable_transcript"] = "\n".join(lines)
    return info
