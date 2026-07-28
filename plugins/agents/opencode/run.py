"""Run `opencode run --format json` and translate its stream as it arrives.

opencode prints JSON lines, which are unreadable in a terminal. This wrapper is
what the platform launches: it writes the normalized event file the dashboard
tails and prints a readable transcript to the PTY.

Signals are forwarded, so stopping a task from the dashboard stops the agent, and
the wrapper exits with opencode's own status.
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
    part = frame.get("part") or {}
    if kind == "text":
        return str(part.get("text") or "")
    if kind == "reasoning":
        text = str(part.get("text") or "")
        return f"\u2026 {text}" if text else ""
    if kind in {"tool_use", "tool"}:
        state = part.get("state") or {}
        name = str(part.get("tool") or state.get("title") or "tool")
        status = str(state.get("status") or "")
        if status in {"pending", "running"}:
            return f"\u2192 {name}({json.dumps(state.get('input') or {}, ensure_ascii=False)[:400]})"
        output = state.get("output")
        text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
        mark = "\u2713" if status == "completed" else "\u2717"
        return f"{mark} {name}: {str(text)[:600]}"
    if kind == "step_finish":
        tokens = part.get("tokens") or {}
        return (f"[opencode] step {part.get('reason', '')} \u00b7 "
                f"{tokens.get('input', 0)} in / {tokens.get('output', 0)} out")
    if kind in {"error", "session_error"}:
        return f"[opencode] error: {json.dumps(frame.get('error') or {})[:500]}"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default="")
    parser.add_argument("opencode", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    argv = [word for word in args.opencode if word != "--"]
    events_path = Path(args.events)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path = Path(args.prompt)
    prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.is_file() else ""

    translator = events_mod.Translator(args.model, events_mod.installed_version(argv[0]))
    sink = events_path.open("a", encoding="utf-8")

    def emit(event: dict) -> None:
        sink.write(json.dumps(event, ensure_ascii=False) + "\n")
        sink.flush()

    emit(translator.start())
    emit(translator.prompt(prompt_text))
    print(f"[opencode] {' '.join(argv[:4])} \u2026", flush=True)

    with open(os.devnull, "rb") as devnull:
        proc = subprocess.Popen(
            [*argv, prompt_text], stdin=devnull, stdout=subprocess.PIPE,
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
        if not stripped.startswith("{"):
            if stripped:
                print(stripped, flush=True)
            continue
        try:
            frame = json.loads(stripped)
        except ValueError:
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
    print(f"[opencode] exited with status {code}", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
