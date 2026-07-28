"""Run Junie CLI on one task and translate its output as it arrives.

Junie has two modes. `--prompt` opens the interactive terminal interface with the
text already submitted; `--task` runs the task and exits. The platform gives an
agent no terminal to answer, so the interactive mode ended the session in a few
seconds without touching the repository — this wrapper uses `--task` and reads
the JSON stream Junie prints with `--output-format json-stream`.

Junie's frames go through the translator into the normalized file the dashboard
tails, and a one-line summary of each step is printed for the terminal view.
Signals are forwarded, so stopping a task from the dashboard stops the agent, and
the wrapper exits with Junie's own status.

Junie ends the whole task when one model request fails, where the other adapters'
tools retry internally. A failure a fresh request could survive is therefore
retried here, resuming the session Junie recorded, up to `--retries` times.
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
    """One line for the terminal view, from one streamed frame."""
    kind = str(frame.get("type") or "")
    if kind == "session":
        return f"[junie] session {frame.get('sessionId', '')}"
    if kind == "step":
        name = str(frame.get("name") or "").strip().replace("\n", " ")
        details = str(frame.get("details") or "").strip().splitlines()
        head = details[0][:160] if details else ""
        return f"\u2192 {name[:120]}" + (f" \u2014 {head}" if head else "")
    if kind == "result":
        return "[junie] task finished"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default="")
    parser.add_argument("--junie-home", required=True)
    parser.add_argument("--session-file", default="",
                        help="where to record the session id, so a follow-up can resume it")
    parser.add_argument("--retries", type=int, default=2,
                        help="resume attempts after a failure a fresh request could survive")
    parser.add_argument("junie", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    argv = [word for word in args.junie if word != "--"]
    if not argv:
        print("[junie] no command to run", flush=True)
        return 2
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

    state = {"recorded": "", "stopped": False}

    def attempt(command: list[str]) -> tuple[int, str]:
        """One Junie invocation. Returns its status and what it printed."""
        print(f"[junie] {' '.join(command[:5])} \u2026", flush=True)
        with open(os.devnull, "rb") as devnull:
            proc = subprocess.Popen(
                [*command, "--task", prompt_text], stdin=devnull, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                bufsize=1, env=os.environ.copy(),
            )

        def forward(signum, _frame):
            # An operator stopping the run must not be read as a failure to retry.
            state["stopped"] = True
            if proc.poll() is None:
                proc.send_signal(signum)

        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            try:
                signal.signal(sig, forward)
            except (ValueError, OSError):
                pass

        assert proc.stdout is not None
        seen: list[str] = []
        for line in proc.stdout:
            stripped = line.rstrip("\n")
            seen.append(stripped)
            if not stripped.lstrip().startswith("{"):
                if stripped.strip():
                    print(stripped, flush=True)
                continue
            try:
                frame = json.loads(stripped.strip())
            except ValueError:
                print(stripped, flush=True)
                continue
            for event in translator.feed(stripped):
                emit(event)
            if translator.session_id and translator.session_id != state["recorded"] and args.session_file:
                state["recorded"] = translator.session_id
                Path(args.session_file).write_text(state["recorded"], encoding="utf-8")
            text = _readable(frame)
            if text:
                print(text, flush=True)
        return proc.wait(), "\n".join(seen[-400:])

    command = list(argv)
    code, output = attempt(command)
    for retry in range(1, max(args.retries, 0) + 1):
        if code == 0 or state["stopped"] or not events_mod.looks_transient(output):
            break
        session_id = state["recorded"]
        if not session_id:
            break  # nothing to resume: the failure came before Junie opened a session
        note = f"[junie] retry {retry} of {args.retries}: resuming session {session_id}"
        print(note, flush=True)
        for event in translator.system(note):
            emit(event)
        command = [*argv, "--session-id", session_id] if "--session-id" not in argv else list(argv)
        code, output = attempt(command)

    for event in translator.shutdown("completed" if code == 0 else f"exit {code}"):
        emit(event)
    sink.close()
    if translator.changed_files:
        print(f"[junie] changed: {', '.join(translator.changed_files[:20])}", flush=True)
    print(f"[junie] exited with status {code}", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
