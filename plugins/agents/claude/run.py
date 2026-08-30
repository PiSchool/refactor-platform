"""Run `claude -p --output-format stream-json` and translate its stream live.

Claude Code prints JSON lines, which are unreadable in a terminal. This wrapper
is what the platform launches: it writes the normalized event file the dashboard
tails and prints a readable transcript to the PTY.

Signals are forwarded, so stopping a task from the dashboard stops the agent, and
the wrapper exits with Claude Code's own status. Standard input is closed rather
than inherited: `claude -p` waits three seconds for piped input otherwise.
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
    if kind == "system":
        if str(frame.get("subtype", "")) == "init":
            return f"[claude] session on {frame.get('model', 'model')}"
        return ""
    if kind == "result":
        usage = frame.get("usage") or {}
        state = "error" if frame.get("is_error") else "ok"
        return (f"[claude] finished {state} · {frame.get('num_turns', 0)} turns · "
                f"{usage.get('input_tokens', 0)} in / {usage.get('output_tokens', 0)} out")
    message = frame.get("message") or {}
    blocks = message.get("content")
    if not isinstance(blocks, list):
        return ""
    out: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type", ""))
        if block_type == "text":
            out.append(str(block.get("text") or ""))
        elif block_type == "thinking":
            text = str(block.get("thinking") or block.get("text") or "")
            if text:
                out.append(f"… {text}")
        elif block_type == "tool_use":
            arguments = json.dumps(block.get("input") or {}, ensure_ascii=False)
            out.append(f"→ {block.get('name', 'tool')}({arguments[:400]})")
        elif block_type == "tool_result":
            content = block.get("content")
            text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            mark = "✗" if block.get("is_error") else "✓"
            out.append(f"{mark} {str(text)[:600]}")
    return "\n".join(part for part in out if part)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default="")
    parser.add_argument("claude", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    argv = [word for word in args.claude if word != "--"]
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
    print(f"[claude] {' '.join(argv[:4])} …", flush=True)

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
    print(f"[claude] exited with status {code}", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
