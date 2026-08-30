"""Junie CLI streamed output translated into the platform's event vocabulary.

Junie runs a task without a terminal when it is given `--task`, and with
`--output-format json-stream` it prints one JSON object per line:

    {"type":"session","sessionId":"session-260728-003353-1bfc"}
    {"type":"step","name":"Opened file","details":"calc.py"}
    {"type":"step","name":"cat calc.py","details":"…","output":"…"}
    {"type":"step","name":"TASK RESULT","details":"### Summary…"}
    {"type":"result","result":"…","changes":[…],"<usage>":[{"inputTokens":…}]}

A step is one unit of work the agent did, so a step becomes one turn in the
Agent view: what it ran, and what came back. `TASK RESULT` is the agent's own
closing statement, so it is an assistant message rather than a tool call.

The final frame carries the token counts as a list of per-model records. Which
key holds that list differs between builds, so it is found by shape — a list of
objects with `inputTokens` — instead of by name.

Stdlib only: imported by the adapter and by the wrapper process.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

#: Junie names a step for a reader, not for a machine. These prefixes are what
#: it reports for the actions the dashboard groups by; anything else keeps the
#: first word of the step's own name, so an unfamiliar action is still visible.
_ACTIONS: tuple[tuple[str, str], ...] = (
    ("found", "search"),
    ("searched", "search"),
    ("opened file", "view"),
    ("read file", "view"),
    ("viewed", "view"),
    ("edited file", "edit"),
    ("created file", "create"),
    ("deleted file", "delete"),
    ("task result", "answer"),
    ("plan", "plan"),
)
#: A step whose name is a command line rather than a description.
_SHELL = re.compile(r"^(?:sudo\s+)?(?:[\w./-]+/)?(?:python3?|pytest|bash|sh|cat|ls|grep|find|"
                    r"git|make|mvn|gradle|npm|node|pip|sed|awk|head|tail|wc|diff|rm|cp|mv|"
                    r"chmod|mkdir|touch|echo|which|env)\b")

#: The closing statement carries this name.
ANSWER = "answer"


def installed_version(binary: str) -> str:
    """The version the CLI reports, for the session record.

    Read once by the wrapper: without it the run view has no version to show and
    labels the session `v?`. Empty when the command cannot answer.
    """
    import re
    import subprocess

    try:
        done = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=20)
    except Exception:
        return ""
    text = (done.stdout or done.stderr or "").strip()
    # CLIs answer with anything from `1.0.75` to `Junie version: 26.7.20 (2383.10)`;
    # the run view shows the number, not the sentence around it.
    found = re.search(r"\d+(?:\.\d+)+[\w.+-]*", text)
    if found:
        return found.group(0)[:40]
    lines = text.splitlines()
    return lines[0].strip()[:40] if lines else ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def action_of(name: str) -> str:
    """What kind of step this is, from the name Junie gave it."""
    lowered = name.strip().lower()
    for prefix, action in _ACTIONS:
        if lowered.startswith(prefix):
            return action
    if _SHELL.match(lowered):
        return "bash"
    first = lowered.split()[0] if lowered.split() else "step"
    return re.sub(r"[^a-z0-9_]+", "_", first).strip("_") or "step"


def _usage_records(frame: dict) -> list[dict]:
    """The per-model token records in a result frame, wherever they are kept."""
    for value in frame.values():
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            if any("inputTokens" in item or "input_tokens" in item for item in value):
                return value
    return []


class Translator:
    def __init__(self, model: str, version: str = "") -> None:
        self.model = model
        self.version = version
        self.session_id = ""
        self.turn = -1
        self.turn_open = False
        self.tokens_input = 0
        self.tokens_output = 0
        self.tokens_cache_read = 0
        self.tokens_reasoning = 0
        self.calls = 0
        self.changed_files: list[str] = []
        self.last_message = ""
        self.errors: list[str] = []
        self.eval_tool_invocations = 0
        self.mcp_invocations = 0

    def _event(self, type_: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"type": type_, "timestamp": now_iso(), "data": data}

    def _open_turn(self) -> Iterator[dict[str, Any]]:
        if self.turn_open:
            return
        self.turn += 1
        self.turn_open = True
        yield self._event("assistant.turn_start", {"turnId": str(self.turn)})

    def _close_turn(self) -> Iterator[dict[str, Any]]:
        if not self.turn_open:
            return
        self.turn_open = False
        yield self._event("assistant.turn_end", {"turnId": str(self.turn)})

    def start(self) -> dict[str, Any]:
        return self._event("session.start", {
            "producer": "junie", "selectedModel": self.model, "version": self.version,
        })

    def prompt(self, text: str) -> dict[str, Any]:
        return self._event("user.message", {"content": text[:4000]})

    def system(self, text: str) -> Iterator[dict[str, Any]]:
        """A note from the wrapper rather than from the model, such as a retry.

        Any open turn is closed first, so the note is a step of its own instead of
        appearing as something the agent did.
        """
        yield from self._close_turn()
        yield self._event("system.message", {"content": str(text)[:4000]})

    def feed(self, line: str) -> Iterator[dict[str, Any]]:
        line = line.strip()
        if not line.startswith("{"):
            return
        try:
            frame = json.loads(line)
        except ValueError:
            return
        if not isinstance(frame, dict):
            return
        kind = str(frame.get("type") or "")

        if kind == "session":
            self.session_id = str(frame.get("sessionId") or "")
            return
        if kind == "step":
            yield from self._step(frame)
            return
        if kind == "result":
            yield from self._result(frame)
            return
        if "error" in kind.lower() or frame.get("error"):
            message = str(frame.get("error") or frame.get("message") or json.dumps(frame))[:4000]
            self.errors.append(message)
            yield self._event("system.message", {"content": message})

    def _step(self, frame: dict) -> Iterator[dict[str, Any]]:
        name = str(frame.get("name") or "step").strip()
        details = str(frame.get("details") or "")
        output = frame.get("output")
        action = action_of(name)

        if action == ANSWER:
            self.last_message = details or self.last_message
            yield from self._open_turn()
            yield self._event("assistant.message", {
                "turnId": str(self.turn), "content": details[:20000], "outputTokens": 0,
            })
            yield from self._close_turn()
            return

        self.calls += 1
        call_id = f"step_{self.calls}"
        if action == "bash" and "eval.sh" in name:
            self.eval_tool_invocations += 1
        if "codebase" in name.lower() or name.lower().startswith("mcp"):
            self.mcp_invocations += 1
        yield from self._open_turn()
        yield self._event("tool.execution_start", {
            "turnId": str(self.turn), "toolCallId": call_id,
            "toolName": action, "arguments": {"action": name[:400]},
        })
        text = details if not output else f"{details}\n{output}" if details else str(output)
        yield self._event("tool.execution_complete", {
            "turnId": str(self.turn), "toolCallId": call_id, "toolName": action,
            "success": True, "result": {"content": str(text)[:4000]},
        })
        yield from self._close_turn()

    def _result(self, frame: dict) -> Iterator[dict[str, Any]]:
        text = str(frame.get("result") or "")
        for change in frame.get("changes") or []:
            if isinstance(change, dict):
                path = str(change.get("afterRelativePath")
                           or change.get("beforeRelativePath") or "")
                if path:
                    self.changed_files.append(path)
        for record in _usage_records(frame):
            self.tokens_input += int(record.get("inputTokens")
                                     or record.get("input_tokens") or 0)
            self.tokens_output += int(record.get("outputTokens")
                                      or record.get("output_tokens") or 0)
            self.tokens_cache_read += int(record.get("cacheInputTokens")
                                          or record.get("cache_read") or 0)
            model = str(record.get("model") or "")
            if model:
                self.model = model
        if text and text != self.last_message:
            self.last_message = text
            yield from self._open_turn()
            yield self._event("assistant.message", {
                "turnId": str(self.turn), "content": text[:20000], "outputTokens": 0,
            })
            yield from self._close_turn()

    def shutdown(self, shutdown_type: str) -> Iterator[dict[str, Any]]:
        yield from self._close_turn()
        yield self._event("session.shutdown", {
            "shutdownType": shutdown_type,
            "currentTokens": self.tokens_input + self.tokens_output,
            "modelMetrics": {self.model or "model": {"usage": {
                "inputTokens": self.tokens_input,
                "outputTokens": self.tokens_output,
                "cacheReadTokens": self.tokens_cache_read,
                "reasoningTokens": self.tokens_reasoning,
            }}},
        })


_AUTH = ("401", "unauthorized", "invalid api key", "authentication", "not authorized")
_RATE = ("429", "rate limit", "quota", "too many requests")
# Junie ends the whole task when one model request fails, and reports it as the
# artifact it could not build ("Failed to build 'issue.md.junie_standalone'").
# Without this the task is recorded as an unexplained failure to apply a change.
_TRANSPORT = ("connection", "timed out", "timeout", "dns", "econnrefused",
              "failed to build '", "llmrequestfailed")
_MODEL = ("model not found", "404", "unknown model",
          "failed to load custom model profile", "profile failed to load")
_STEPS = ("step limit", "maximum number of steps")


def looks_transient(text: str) -> bool:
    """Whether a fresh request could survive this failure.

    A dropped connection, a rate limit and a model request Junie could not build
    are all retryable; a rejected key, an unknown model and the step limit are
    not, and retrying them wastes the task's time budget.
    """
    low = text.lower()
    if any(token in low for token in _AUTH + _MODEL + _STEPS):
        return False
    return any(token in low for token in _TRANSPORT + _RATE)


def parse(events_path: Path | None, terminal_log_path: Path, requested_model: str) -> dict:
    """Read the normalized file back into the platform's SessionInfo shape."""
    info: dict[str, Any] = {
        "tokens_input": 0, "tokens_output": 0, "tokens_cache_read": 0,
        "tokens_reasoning": 0, "context_tokens": 0, "model": requested_model,
        "response_text": "", "readable_transcript": "", "flags": set(),
        "eval_tool_invocations": 0, "retrieval_invocations": 0,
    }
    completed = False
    rows: list[dict[str, Any]] = []
    if events_path and events_path.is_file():
        for raw in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(raw))
            except ValueError:
                continue
    lines: list[str] = []
    errors: list[str] = []
    for row in rows:
        kind = str(row.get("type", ""))
        data = row.get("data") or {}
        if kind == "session.start":
            info["model"] = str(data.get("selectedModel") or requested_model)
        elif kind == "assistant.message":
            content = str(data.get("content") or "")
            if content:
                info["response_text"] = content
                lines.append(content)
        elif kind == "tool.execution_start":
            name = str(data.get("toolName") or "")
            arguments = json.dumps(data.get("arguments") or {})[:400]
            lines.append(f"\u2192 {name}({arguments})")
            if "eval.sh" in arguments:
                info["eval_tool_invocations"] += 1
            if "codebase" in arguments.lower():
                info["retrieval_invocations"] += 1
        elif kind == "system.message":
            errors.append(str(data.get("content") or ""))
        elif kind == "session.shutdown":
            completed = str(data.get("shutdownType") or "") == "completed"
            for usage in (data.get("modelMetrics") or {}).values():
                measured = usage.get("usage") or {}
                info["tokens_input"] += int(measured.get("inputTokens") or 0)
                info["tokens_output"] += int(measured.get("outputTokens") or 0)
                info["tokens_cache_read"] += int(measured.get("cacheReadTokens") or 0)
                info["tokens_reasoning"] += int(measured.get("reasoningTokens") or 0)
            info["context_tokens"] = int(data.get("currentTokens") or 0)

    haystack = " ".join(errors).lower()
    if terminal_log_path.is_file():
        haystack += " " + terminal_log_path.read_text(
            encoding="utf-8", errors="replace")[-8000:].lower()
    if any(token in haystack for token in _AUTH):
        info["flags"].add("auth_wall")
    # A transport failure or a rate limit that a retry got past is history, not
    # the outcome: flagging a completed session with it would name a provider
    # error as the reason a task that finished did not pass.
    if not completed and any(token in haystack for token in _RATE):
        info["flags"].add("rate_limited")
    if not completed and any(token in haystack for token in _TRANSPORT):
        info["flags"].add("provider_error")
    if any(token in haystack for token in _MODEL):
        info["flags"].add("model_unavailable")
    if any(token in haystack for token in _STEPS):
        info["flags"].add("step_limit")
    info["readable_transcript"] = "\n".join(lines)[:200_000]
    return info
