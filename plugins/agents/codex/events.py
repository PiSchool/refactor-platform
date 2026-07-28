"""Codex `exec --json` items translated into the platform's event vocabulary.

Codex reports a thread, turns, and items (`agent_message`, `reasoning`,
`command_execution`, `file_change`, `mcp_tool_call`, `error`). The dashboard
reads `session.*`, `assistant.*` and `tool.*` events, so the translation happens
here — once, in the adapter — and both the live view and `parse_session` read
the same normalized file.

Stdlib only: this module is imported by the adapter and by the wrapper process.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

TOOL_ITEMS = {"command_execution", "file_change", "mcp_tool_call", "web_search"}


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
    """Codex JSONL in, platform events out.

    A codex `exec` run is one long turn, which would collapse the Agent view
    into a single group. A UI turn is closed after each agent message instead,
    so a group is one reasoning/tool/answer cluster.
    """

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
        self.command_count = 0
        self.eval_tool_invocations = 0
        self.mcp_invocations = 0
        self.file_changes = 0

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

    def _tool(self, call_id: str, name: str, arguments: dict[str, Any],
              ok: bool, output: str) -> Iterator[dict[str, Any]]:
        yield from self._open_turn()
        yield self._event("tool.execution_start", {
            "turnId": str(self.turn), "toolCallId": call_id,
            "toolName": name, "arguments": arguments,
        })
        yield self._event("tool.execution_complete", {
            "turnId": str(self.turn), "toolCallId": call_id,
            "success": ok, "result": {"content": output[:4000]},
        })

    # -- entry points ----------------------------------------------------
    def start(self) -> dict[str, Any]:
        return self._event("session.start", {
            "producer": "codex", "selectedModel": self.model, "version": self.version,
        })

    def prompt(self, text: str) -> dict[str, Any]:
        return self._event("user.message", {"content": text[:4000]})

    def feed(self, line: str) -> Iterator[dict[str, Any]]:
        """One line of codex JSONL to zero or more platform events."""
        line = line.strip()
        if not line:
            return
        try:
            frame = json.loads(line)
        except ValueError:
            return
        kind = str(frame.get("type", ""))
        if kind == "turn.started":
            yield from self._open_turn()
            return
        if kind == "turn.completed":
            usage = frame.get("usage") or {}
            self.tokens_input += int(usage.get("input_tokens") or 0)
            self.tokens_output += int(usage.get("output_tokens") or 0)
            self.tokens_cache_read += int(usage.get("cached_input_tokens") or 0)
            self.tokens_reasoning += int(usage.get("reasoning_output_tokens") or 0)
            yield from self._close_turn()
            return
        if kind == "turn.failed":
            self.errors.append(str((frame.get("error") or {}).get("message") or "turn failed"))
            yield from self._close_turn()
            return
        if kind not in {"item.completed", "item.started"}:
            return

        item = frame.get("item") or {}
        item_type = str(item.get("type", ""))
        item_id = str(item.get("id") or f"item_{self.turn}")
        if kind == "item.started":
            # Only long-running items are worth announcing before they finish.
            if item_type == "command_execution":
                yield from self._open_turn()
                yield self._event("tool.execution_start", {
                    "turnId": str(self.turn), "toolCallId": item_id,
                    "toolName": "bash", "arguments": {"command": item.get("command", "")},
                })
            return

        if item_type == "agent_message":
            text = str(item.get("text") or "")
            self.last_message = text or self.last_message
            yield from self._open_turn()
            yield self._event("assistant.message", {
                "turnId": str(self.turn), "content": text, "outputTokens": 0,
            })
            yield from self._close_turn()
            return
        if item_type == "reasoning":
            text = str(item.get("text") or "")
            if text:
                yield from self._open_turn()
                yield self._event("assistant.message", {
                    "turnId": str(self.turn), "content": f"reasoning: {text}", "outputTokens": 0,
                })
            return
        if item_type == "command_execution":
            command = str(item.get("command") or "")
            exit_code = item.get("exit_code")
            ok = exit_code in (0, None) and str(item.get("status", "")) != "failed"
            self.command_count += 1
            if "eval.sh" in command:
                self.eval_tool_invocations += 1
            yield from self._open_turn()
            yield self._event("tool.execution_start", {
                "turnId": str(self.turn), "toolCallId": item_id,
                "toolName": "bash", "arguments": {"command": command},
            })
            yield self._event("tool.execution_complete", {
                "turnId": str(self.turn), "toolCallId": item_id, "success": ok,
                "result": {"content": str(item.get("aggregated_output") or "")[:4000]},
            })
            return
        if item_type == "file_change":
            changes = item.get("changes") or []
            self.file_changes += len(changes) if isinstance(changes, list) else 1
            yield from self._tool(item_id, "edit", {"changes": changes},
                                  str(item.get("status", "")) != "failed", "")
            return
        if item_type == "mcp_tool_call":
            self.mcp_invocations += 1
            name = f"{item.get('server', 'mcp')}.{item.get('tool', 'call')}"
            ok = str(item.get("status", "")) not in {"failed", "error"}
            yield from self._tool(item_id, name, item.get("arguments") or {}, ok,
                                  json.dumps(item.get("result") or "")[:4000])
            return
        if item_type == "error":
            message = str(item.get("message") or "")
            self.errors.append(message)
            yield self._event("system.message", {"content": message})
            return
        if item_type == "web_search":
            yield from self._tool(item_id, "web_search", {"query": item.get("query", "")}, True, "")

    def shutdown(self, shutdown_type: str) -> Iterator[dict[str, Any]]:
        yield from self._close_turn()
        yield self._event("session.shutdown", {
            "shutdownType": shutdown_type,
            "currentTokens": 0,
            "modelMetrics": {self.model or "model": {"usage": {
                "inputTokens": self.tokens_input,
                "outputTokens": self.tokens_output,
                "cacheReadTokens": self.tokens_cache_read,
                "reasoningTokens": self.tokens_reasoning,
            }}},
        })


_AUTH = ("401", "unauthorized", "invalid api key", "authentication")
_RATE = ("429", "rate limit", "quota", "too many requests")
_TRANSPORT = ("connection", "timed out", "timeout", "dns", "econnrefused", "stream disconnected")


def parse(events_path: Path | None, terminal_log_path: Path, requested_model: str):
    """Read the normalized file back into the platform's SessionInfo shape.

    Returned as a plain dict so this module stays importable from the wrapper
    process, which has no reason to depend on the SDK.
    """
    info = {
        "tokens_input": 0, "tokens_output": 0, "tokens_cache_read": 0,
        "tokens_reasoning": 0, "context_tokens": 0, "model": requested_model,
        "response_text": "", "readable_transcript": "", "flags": set(),
        "eval_tool_invocations": 0, "retrieval_invocations": 0,
        "compaction_count": 0, "context_overflow_count": 0,
    }
    lines: list[str] = []
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    if events_path and events_path.is_file():
        for raw in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(raw))
            except ValueError:
                continue
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
            args = json.dumps(data.get("arguments") or {})[:400]
            lines.append(f"→ {name}({args})")
            if name == "bash" and "eval.sh" in args:
                info["eval_tool_invocations"] += 1
            if name.startswith("codebase-retrieval."):
                info["retrieval_invocations"] += 1
        elif kind == "system.message":
            errors.append(str(data.get("content") or ""))
        elif kind == "session.shutdown":
            for usage in (data.get("modelMetrics") or {}).values():
                u = usage.get("usage") or {}
                info["tokens_input"] += int(u.get("inputTokens") or 0)
                info["tokens_output"] += int(u.get("outputTokens") or 0)
                info["tokens_cache_read"] += int(u.get("cacheReadTokens") or 0)
                info["tokens_reasoning"] += int(u.get("reasoningTokens") or 0)
            info["context_tokens"] = int(data.get("currentTokens") or 0)

    haystack = " ".join(errors).lower()
    if not rows and terminal_log_path.is_file():
        haystack += " " + terminal_log_path.read_text(encoding="utf-8", errors="replace")[-8000:].lower()
    if any(token in haystack for token in _AUTH):
        info["flags"].add("auth_wall")
    if any(token in haystack for token in _RATE):
        info["flags"].add("rate_limited")
    if any(token in haystack for token in _TRANSPORT):
        info["flags"].add("transport_error")
    info["readable_transcript"] = "\n".join(lines)
    return info
