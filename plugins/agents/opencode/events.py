"""opencode `run --format json` translated into the platform's event vocabulary.

opencode emits one JSON object per line, each wrapping a `part`: `step_start`
opens a model step, `text` and `reasoning` carry the assistant's words,
`tool_use` reports a call with its input, output and status, and `step_finish`
closes the step with its token counts and stop reason.

A UI turn is one model step, so the Agent view groups a reasoning/tool/answer
cluster rather than collapsing the session into a single block.

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
        self.tokens_reasoning = 0
        self.last_message = ""
        self.errors: list[str] = []
        self.eval_tool_invocations = 0
        self.mcp_invocations = 0
        self._started: set[str] = set()

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
            "producer": "opencode", "selectedModel": self.model,
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
        part = frame.get("part") or {}
        if kind == "step_start":
            yield from self._open_turn()
        elif kind == "text":
            text = str(part.get("text") or "")
            if text:
                self.last_message = text
                yield from self._open_turn()
                yield self._event("assistant.message", {
                    "turnId": str(self.turn), "content": text, "outputTokens": 0,
                })
        elif kind == "reasoning":
            text = str(part.get("text") or "")
            if text:
                yield from self._open_turn()
                yield self._event("assistant.message", {
                    "turnId": str(self.turn), "content": f"reasoning: {text}", "outputTokens": 0,
                })
        elif kind in {"tool_use", "tool"}:
            yield from self._tool(part)
        elif kind == "step_finish":
            tokens = part.get("tokens") or {}
            cache = tokens.get("cache") or {}
            self.tokens_input += int(tokens.get("input") or 0)
            self.tokens_output += int(tokens.get("output") or 0)
            self.tokens_reasoning += int(tokens.get("reasoning") or 0)
            self.tokens_cache_read += int(cache.get("read") or 0)
            if str(part.get("reason") or "") == "error":
                self.errors.append("model step ended in an error")
            yield from self._close_turn()
        elif kind in {"error", "session_error"}:
            message = json.dumps(frame.get("error") or frame.get("part") or {})[:2000]
            self.errors.append(message)
            yield self._event("system.message", {"content": message})

    def _tool(self, part: dict) -> Iterator[dict[str, Any]]:
        state = part.get("state") or {}
        status = str(state.get("status") or "")
        name = str(part.get("tool") or state.get("title") or "tool")
        call_id = str(part.get("callID") or part.get("id") or f"tool_{self.turn}")
        arguments = state.get("input") or {}
        if call_id not in self._started:
            self._started.add(call_id)
            if name.startswith("mcp_") or name.startswith("codebase"):
                self.mcp_invocations += 1
            if "eval.sh" in json.dumps(arguments):
                self.eval_tool_invocations += 1
            yield from self._open_turn()
            yield self._event("tool.execution_start", {
                "turnId": str(self.turn), "toolCallId": call_id,
                "toolName": name, "arguments": arguments,
            })
        if status in {"completed", "error"}:
            output = state.get("output")
            text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            yield self._event("tool.execution_complete", {
                "turnId": str(self.turn), "toolCallId": call_id, "toolName": name,
                "success": status == "completed", "result": {"content": str(text)[:4000]},
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
                "reasoningTokens": self.tokens_reasoning,
            }}},
        })


_AUTH = ("401", "unauthorized", "invalid api key", "authentication")
_RATE = ("429", "rate limit", "quota", "too many requests")
_TRANSPORT = ("connection", "timed out", "timeout", "dns", "econnrefused", "fetch failed")
_MODEL = ("model not found", "404", "unknown model")


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
            lines.append(f"\u2192 {name}({arguments})")
            if "eval.sh" in arguments:
                info["eval_tool_invocations"] += 1
            if name.startswith("mcp_") or name.startswith("codebase"):
                info["retrieval_invocations"] += 1
        elif kind == "system.message":
            errors.append(str(data.get("content") or ""))
        elif kind == "session.shutdown":
            for usage in (data.get("modelMetrics") or {}).values():
                measured = usage.get("usage") or {}
                info["tokens_input"] += int(measured.get("inputTokens") or 0)
                info["tokens_output"] += int(measured.get("outputTokens") or 0)
                info["tokens_cache_read"] += int(measured.get("cacheReadTokens") or 0)
                info["tokens_reasoning"] += int(measured.get("reasoningTokens") or 0)
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
