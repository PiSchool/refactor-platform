"""Run `codex exec --json` and translate its stream as it arrives.

Codex reports structured progress on stdout as JSON lines, which is unreadable
in a terminal, and keeps its own session state in a private database. This
wrapper is what the platform launches: it feeds the prompt on stdin, writes the
normalized event file the dashboard tails, and prints a readable transcript to
the PTY.

Signals are forwarded to codex so stopping a task from the dashboard stops the
agent, and the wrapper exits with codex's own status.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import events as events_mod  # noqa: E402


def _readable(frame: dict) -> str:
    kind = str(frame.get("type", ""))
    item = frame.get("item") or {}
    item_type = str(item.get("type", ""))
    if kind == "thread.started":
        return f"[codex] thread {frame.get('thread_id', '')}"
    if kind == "turn.started":
        return "[codex] turn started"
    if kind == "turn.completed":
        usage = frame.get("usage") or {}
        return (f"[codex] turn completed · {usage.get('input_tokens', 0)} in / "
                f"{usage.get('output_tokens', 0)} out")
    if kind == "turn.failed":
        return f"[codex] turn failed: {(frame.get('error') or {}).get('message', '')}"
    if kind == "item.started" and item_type == "command_execution":
        return f"$ {item.get('command', '')}"
    if kind != "item.completed":
        return ""
    if item_type == "agent_message":
        return str(item.get("text") or "")
    if item_type == "reasoning":
        return f"… {item.get('text', '')}"
    if item_type == "command_execution":
        out = str(item.get("aggregated_output") or "").rstrip()
        head = f"$ {item.get('command', '')} → exit {item.get('exit_code')}"
        return f"{head}\n{out}" if out else head
    if item_type == "file_change":
        paths = ", ".join(str(c.get("path", "")) for c in (item.get("changes") or [])
                          if isinstance(c, dict))
        return f"~ edit {paths}"
    if item_type == "mcp_tool_call":
        return f"→ {item.get('server', 'mcp')}.{item.get('tool', 'call')}"
    if item_type == "error":
        return f"[codex] error: {item.get('message', '')}"
    if item_type == "web_search":
        return f"→ web_search({item.get('query', '')})"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="")
    ap.add_argument("codex", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    codex_argv = [a for a in args.codex if a != "--"]
    events_path = Path(args.events)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path = Path(args.prompt)
    prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.is_file() else ""

    translator = events_mod.Translator(args.model, events_mod.installed_version(codex_argv[0]))
    sink = events_path.open("a", encoding="utf-8")

    def emit(event: dict) -> None:
        sink.write(json.dumps(event, ensure_ascii=False) + "\n")
        sink.flush()

    emit(translator.start())
    emit(translator.prompt(prompt_text))
    print(f"[codex] {' '.join(codex_argv[:6])} …", flush=True)

    with prompt_path.open("rb") as stdin_file:
        proc = subprocess.Popen(
            codex_argv, stdin=stdin_file, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
            bufsize=1, env=os.environ.copy(),
        )

    def forward(signum, _frame):
        if proc.poll() is None:
            proc.send_signal(signum)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, forward)
        except (ValueError, OSError):
            pass

    assert proc.stdout is not None
    for line in proc.stdout:
        stripped = line.rstrip("\n")
        frame = None
        if stripped.startswith("{"):
            try:
                frame = json.loads(stripped)
            except ValueError:
                frame = None
        if frame is None:
            print(stripped, flush=True)
            continue
        for event in translator.feed(stripped):
            emit(event)
        text = _readable(frame)
        if text:
            print(text, flush=True)

    code = proc.wait()
    for event in translator.shutdown("completed" if code == 0 else f"exit {code}"):
        emit(event)
    sink.close()
    print(f"[codex] finished with status {code}", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
