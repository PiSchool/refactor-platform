"""Scripted fake agent CLI: edits a file in the workspace, writes a fake
events.jsonl, prints ANSI output, exits. Proves the platform's run
infrastructure without a real model.

Usage: stub_cli.py <workspace> <events_path> [--sleep N] [--noedit]
"""
import json
import sys
import time
from pathlib import Path


def main() -> int:
    ws = Path(sys.argv[1])
    events_path = Path(sys.argv[2])
    sleep = 0.0
    edit = True
    for i, a in enumerate(sys.argv):
        if a == "--sleep":
            sleep = float(sys.argv[i + 1])
        if a == "--noedit":
            edit = False

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
        {"type": "assistant.message", "data": {"content": "I appended the line. DONE"}},
        {"type": "session.shutdown", "data": {"modelMetrics": {
            "stub-model": {"usage": {"inputTokens": 100, "outputTokens": 50}}}}},
    ]
    events_path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    print("\x1b[32m[stub]\x1b[0m done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
