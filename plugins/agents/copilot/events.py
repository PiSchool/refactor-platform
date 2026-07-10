"""Parse Copilot CLI events.jsonl into a SessionInfo.

Authoritative token totals come from session.shutdown.modelMetrics; response
text from assistant.message; diagnostic flags from recognized markers.
Ported from the validated POC events parser.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.catalog.sdk import SessionInfo

_AUTH_WALL = (
    "/login", "sign in to use copilot", "sign in to github", "please use /login",
    "please run: copilot login", "run `copilot auth`", "not authenticated",
    "authentication failed", "unauthorized to access this resource",
)
_RATE_LIMIT = ("rate limit", "rate-limited", "too many requests", "429", "quota")
_TRANSPORT = ("transport error", "connection reset", "econnreset", "socket hang up",
              "network error", "fetch failed", "err_")


def _iter_events(path: Path):
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def parse(events_path: Path | None, terminal_log: Path | None, requested_model: str = "") -> SessionInfo:
    info = SessionInfo(model=requested_model)
    if events_path is None or not events_path.is_file():
        info.flags |= _scan_terminal(terminal_log)
        return info

    assistant_parts: list[str] = []
    transcript: list[str] = []
    parsed_model = ""
    for ev in _iter_events(events_path):
        etype = ev.get("type", "")
        data = ev.get("data", {}) or {}
        if etype == "assistant.message":
            content = str(data.get("content", "") or "")
            if content.strip():
                assistant_parts.append(content)
                transcript.append(f"[assistant] {content}")
        elif etype == "user.message":
            transcript.append(f"[user] {str(data.get('content', '') or '')}")
        elif etype == "tool.execution_start":
            tool = str(data.get("toolName", "") or "")
            args = str(data.get("arguments", data.get("command", "")) or "")
            transcript.append(f"[tool:{tool}] {args}")
            if "eval.sh" in args:
                info.eval_iterations += 1
        elif etype == "session.compaction_complete":
            # the agent hit its context window and summarised the conversation
            if data.get("success", True):
                info.compaction_count += 1
        elif etype == "session.error":
            if _is_context_overflow(data):
                info.context_overflow_count += 1
        elif etype == "session.shutdown":
            mm = data.get("modelMetrics", {}) or {}
            for model_name, metrics in mm.items():
                parsed_model = model_name
                usage = metrics.get("usage", {}) or {}
                info.tokens_input += int(usage.get("inputTokens", 0) or 0)
                info.tokens_output += int(usage.get("outputTokens", 0) or 0)
                # cacheRead ⊆ input and reasoning ⊆ output (the CLI prints
                # "↑ 720.9k (209.2k cached) · ↓ 6.2k (2.2k reasoning)")
                info.tokens_cache_read += int(usage.get("cacheReadTokens", 0) or 0)
                info.tokens_reasoning += int(usage.get("reasoningTokens", 0) or 0)
            # context occupancy at the end, not the window size
            info.context_tokens = int(data.get("currentTokens", 0) or 0)

    if parsed_model:
        info.model = parsed_model
        if requested_model and _base_model(requested_model) != _base_model(parsed_model):
            info.flags.add("model_mismatch")
    info.response_text = assistant_parts[-1] if assistant_parts else ""
    info.readable_transcript = "\n\n".join(transcript)
    info.flags |= _scan_terminal(terminal_log)
    return info


_OVERFLOW_MARKERS = (
    "context length", "context_length", "maximum context", "context window",
    "too many tokens", "prompt is too long", "request too large",
)


def _is_context_overflow(data: dict) -> bool:
    """The provider rejected a request because the prompt exceeded the window.

    There is no dedicated event for this — it arrives as a `session.error`
    whose message names the context limit, so match on that.
    """
    message = str(data.get("message", "") or "").lower()
    return any(marker in message for marker in _OVERFLOW_MARKERS)


def _base_model(m: str) -> str:
    return m.strip().lower().split("/")[-1]


def _scan_terminal(terminal_log: Path | None) -> set[str]:
    flags: set[str] = set()
    if terminal_log is None or not terminal_log.is_file():
        return flags
    text = terminal_log.read_bytes().decode("utf-8", errors="ignore").lower()
    if any(m in text for m in _AUTH_WALL):
        flags.add("auth_wall")
    if any(m in text for m in _RATE_LIMIT):
        flags.add("rate_limited")
    if any(m in text for m in _TRANSPORT):
        flags.add("transport_error")
    return flags
