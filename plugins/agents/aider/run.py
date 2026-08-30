"""Run aider once and translate its printed report as it arrives.

Aider prints its progress; this wrapper is what the platform launches. It
mirrors every line to the PTY unchanged and writes the normalized event file
the dashboard tails, so the Agent view works the same as for adapters with a
structured stream.

Signals are forwarded so stopping a task stops aider, and the wrapper exits
with aider's own status.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="")
    ap.add_argument("aider", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    aider_argv = [a for a in args.aider if a != "--"]
    events_path = Path(args.events)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path = Path(args.prompt)
    prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.is_file() else ""

    translator = events_mod.Translator(args.model)
    sink = events_path.open("a", encoding="utf-8")

    def emit(event: dict) -> None:
        sink.write(json.dumps(event, ensure_ascii=False) + "\n")
        sink.flush()

    emit(translator.start())
    emit(translator.prompt(prompt_text))
    print(f"[aider] {' '.join(aider_argv[:4])} …", flush=True)

    proc = subprocess.Popen(
        aider_argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
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
        text = line.rstrip("\n")
        print(text, flush=True)
        for event in translator.feed(text):
            emit(event)

    code = proc.wait()
    for event in translator.shutdown("completed" if code == 0 else f"exit {code}"):
        emit(event)
    sink.close()
    print(f"[aider] finished with status {code}", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
