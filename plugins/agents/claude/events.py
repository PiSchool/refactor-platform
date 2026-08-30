"""Claude Code `--output-format stream-json` translated into platform events.

Claude Code emits one JSON object per line: a `system`/`init` frame naming the
model and tools, `assistant` frames whose message content is a list of `text`,
`thinking` and `tool_use` blocks, `user` frames carrying `tool_result` blocks,
and a final `result` frame with usage and the answer.

The dashboard reads `session.*`, `user.*`, `assistant.*` and `tool.*`, so the
translation happens here — once — and both the live view and `parse_session`
read the same normalized file.

A UI turn is closed after each assistant message that is not a tool call, so a
group is one thinking/tool/answer cluster rather than the whole session.

Stdlib only: imported by the adapter and by the wrapper process.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


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


class Translator:
    def __init__(self, model: str, version: str = "") -> None:
        self.model = model
        self.version = version
        self.turn = -1
        self.turn_open = False
        self.tokens_input = 0
        self.tokens_output = 0
        self.tokens_cache_read = 0
        self.last_message = ""
        self.errors: list[str] = []
        self.eval_tool_invocations = 0
        self.mcp_invocations = 0
        #: tool_use id -> tool name, so a result can name the call it answers
        self._pending: dict[str, str] = {}

    # -- helpers ---------------------------------------------------------
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

    # -- entry points ----------------------------------------------------
    def start(self) -> dict[str, Any]:
        return self._event("session.start", {
            "producer": "claude", "selectedModel": self.model,
            "version": self.version,
        })

    def prompt(self, text: str) -> dict[str, Any]:
        return self._event("user.message", {"content": text[:4000]})

    def feed(self, line: str) -> Iterator[dict[str, Any]]:
        line = line.strip()
        if not line.startswith("{"):
            return
        try:
            frame = json.loads(line)
        except ValueError:
            return
        kind = str(frame.get("type", ""))
        if kind == "system":
            if str(frame.get("subtype", "")) == "init" and frame.get("model"):
                self.model = str(frame["model"])
            return
        if kind == "assistant":
            yield from self._assistant(frame.get("message") or {})
            return
        if kind == "user":
            yield from self._results(frame.get("message") or {})
            return
        if kind == "result":
            usage = frame.get("usage") or {}
            self.tokens_input += int(usage.get("input_tokens") or 0)
            self.tokens_output += int(usage.get("output_tokens") or 0)
            self.tokens_cache_read += int(usage.get("cache_read_input_tokens") or 0)
            if frame.get("is_error"):
                self.errors.append(str(frame.get("result") or "agent reported an error"))
            answer = str(frame.get("result") or "")
            if answer and not frame.get("is_error"):
                self.last_message = answer
            yield from self._close_turn()

    def _assistant(self, message: dict) -> Iterator[dict[str, Any]]:
        usage = message.get("usage") or {}
        # A synthetic message carries no usage and is Claude Code speaking for
        # itself (a transport error, for instance), not the model answering.
        synthetic = str(message.get("model") or "") == "<synthetic>"
        blocks = message.get("content")
        if not isinstance(blocks, list):
            return
        called = False
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type", ""))
            if block_type == "text":
                text = str(block.get("text") or "")
                if not text:
                    continue
                if synthetic:
                    self.errors.append(text)
                    yield self._event("system.message", {"content": text[:4000]})
                    continue
                self.last_message = text
                yield from self._open_turn()
                yield self._event("assistant.message", {
                    "turnId": str(self.turn), "content": text,
                    "outputTokens": int(usage.get("output_tokens") or 0),
                })
            elif block_type == "thinking":
                text = str(block.get("thinking") or block.get("text") or "")
                if text:
                    yield from self._open_turn()
                    yield self._event("assistant.message", {
                        "turnId": str(self.turn), "content": f"reasoning: {text}",
                        "outputTokens": 0,
                    })
            elif block_type == "tool_use":
                called = True
                name = str(block.get("name") or "tool")
                call_id = str(block.get("id") or f"tool_{self.turn}")
                arguments = block.get("input") or {}
                self._pending[call_id] = name
                if name.startswith("mcp__"):
                    self.mcp_invocations += 1
                if "eval.sh" in json.dumps(arguments):
                    self.eval_tool_invocations += 1
                yield from self._open_turn()
                yield self._event("tool.execution_start", {
                    "turnId": str(self.turn), "toolCallId": call_id,
                    "toolName": name, "arguments": arguments,
                })
        if not called and not synthetic:
            yield from self._close_turn()

    def _results(self, message: dict) -> Iterator[dict[str, Any]]:
        blocks = message.get("content")
        if not isinstance(blocks, list):
            return
        for block in blocks:
            if not isinstance(block, dict) or str(block.get("type", "")) != "tool_result":
                continue
            call_id = str(block.get("tool_use_id") or "")
            content = block.get("content")
            text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            yield self._event("tool.execution_complete", {
                "turnId": str(self.turn), "toolCallId": call_id,
                "toolName": self._pending.pop(call_id, ""),
                "success": not block.get("is_error"),
                "result": {"content": str(text)[:4000]},
            })

    def shutdown(self, shutdown_type: str) -> Iterator[dict[str, Any]]:
        yield from self._close_turn()
        yield self._event("session.shutdown", {
            "shutdownType": shutdown_type,
            "currentTokens": self.tokens_input + self.tokens_output,
            "modelMetrics": {self.model or "model": {"usage": {
                "inputTokens": self.tokens_input,
                "outputTokens": self.tokens_output,
                "cacheReadTokens": self.tokens_cache_read,
                "reasoningTokens": 0,
            }}},
        })


_AUTH = ("401", "unauthorized", "invalid api key", "authentication", "apikeysource")
_RATE = ("429", "rate limit", "quota", "too many requests", "overloaded")
_TRANSPORT = ("connection", "timed out", "timeout", "dns", "econnrefused", "socket hang up")
_MODEL = ("model_not_found", "may not have access to it", "404")


def parse(events_path: Path | None, terminal_log_path: Path, requested_model: str) -> dict:
    """Read the normalized file back into the platform's SessionInfo shape."""
    info: dict[str, Any] = {
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
    for row in rows:
        kind = str(row.get("type", ""))
        data = row.get("data") or {}
        if kind == "session.start":
            info["model"] = str(data.get("selectedModel") or requested_model)
        elif kind == "assistant.message":
            content = str(data.get("content") or "")
            if content and not content.startswith("reasoning: "):
                info["response_text"] = content
            if content:
                lines.append(content)
        elif kind == "tool.execution_start":
            name = str(data.get("toolName") or "")
            arguments = json.dumps(data.get("arguments") or {})[:400]
            lines.append(f"→ {name}({arguments})")
            if "eval.sh" in arguments:
                info["eval_tool_invocations"] += 1
            if name.startswith("mcp__"):
                info["retrieval_invocations"] += 1
        elif kind == "system.message":
            errors.append(str(data.get("content") or ""))
        elif kind == "session.shutdown":
            for usage in (data.get("modelMetrics") or {}).values():
                measured = usage.get("usage") or {}
                info["tokens_input"] += int(measured.get("inputTokens") or 0)
                info["tokens_output"] += int(measured.get("outputTokens") or 0)
                info["tokens_cache_read"] += int(measured.get("cacheReadTokens") or 0)
            info["context_tokens"] = int(data.get("currentTokens") or 0)

    haystack = " ".join(errors).lower()
    if not rows and terminal_log_path.is_file():
        haystack += " " + terminal_log_path.read_text(
            encoding="utf-8", errors="replace")[-8000:].lower()
    if any(token in haystack for token in _AUTH):
        info["flags"].add("auth_wall")
    if any(token in haystack for token in _RATE):
        info["flags"].add("rate_limited")
    if any(token in haystack for token in _TRANSPORT):
        info["flags"].add("provider_error")
    if any(token in haystack for token in _MODEL):
        info["flags"].add("model_unavailable")
    info["readable_transcript"] = "\n".join(lines)[:200_000]
    return info
