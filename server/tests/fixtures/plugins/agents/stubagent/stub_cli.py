"""Scripted fake agent CLI: edits a file in the workspace, writes a fake
events.jsonl, prints ANSI output, exits. Proves the platform's run
infrastructure without a real model.

Usage: stub_cli.py <workspace> <events_path> [--sleep N] [--noedit]
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    ws = Path(sys.argv[1])
    events_path = Path(sys.argv[2])
    sleep = 0.0
    edit = True
    setup = "s1"
    corrupt_eval = False
    skip_eval = False
    append_events = False
    for i, a in enumerate(sys.argv):
        if a == "--sleep":
            sleep = float(sys.argv[i + 1])
        if a == "--noedit":
            edit = False
        if a == "--setup":
            setup = sys.argv[i + 1]
        if a == "--corrupt-eval":
            corrupt_eval = True
        if a == "--skip-eval":
            skip_eval = True
        if a == "--append-events":
            append_events = True

    print("\x1b[32m[stub]\x1b[0m starting agent session")
    if sleep:
        time.sleep(sleep)

    if edit:
        target = next(ws.glob("*.py"), None)
        if target is None:
            target = ws / "target.py"
        with target.open("a", encoding="utf-8") as fh:
            fh.write("done\n")
        print(f"[stub] appended to {target.name}")

    events_path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {"type": "session.start", "data": {"sessionId": "stub", "selectedModel": "stub-model"}},
    ]
    if setup == "s1_lsp":
        events.append({"type": "tool.execution_start", "data": {
            "toolName": "lsp", "arguments": {"operation": "hover"}}})
    elif setup == "s1_eval" and not skip_eval:
        events.append({"type": "tool.execution_start", "data": {
            "toolName": "bash", "arguments": {"command": "bash eval.sh"}}})
        checked = subprocess.run(
            ["bash", "eval.sh"], cwd=ws, text=True, capture_output=True, check=False,
            env={**os.environ, **({"RP_PLUGINS_DIR": "/missing-plugins"} if corrupt_eval else {})},
        )
        print(checked.stdout, end="")
        if checked.stderr:
            print(checked.stderr, end="", file=sys.stderr)
    elif setup == "s3":
        events.append({"type": "tool.execution_start", "data": {
            "toolName": "task", "arguments": {"agent": "analyst"}}})
    events.extend([
        {"type": "assistant.message", "data": {"content": "I appended the line. DONE"}},
        {"type": "session.shutdown", "data": {"modelMetrics": {
            "stub-model": {"usage": {"inputTokens": 100, "outputTokens": 50}}}}},
    ])
    mode = "a" if append_events else "w"
    with events_path.open(mode, encoding="utf-8") as handle:
        handle.write("\n".join(json.dumps(e) for e in events) + "\n")
    print("\x1b[32m[stub]\x1b[0m done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
