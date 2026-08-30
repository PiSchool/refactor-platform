"""Small JSON-RPC/LSP server used to prove the platform performs initialize."""
from __future__ import annotations

import json
import sys


def _read_message() -> dict | None:
    length = None
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, _, value = line.decode("ascii").partition(":")
        if name.lower() == "content-length":
            length = int(value.strip())
    if length is None:
        return None
    return json.loads(sys.stdin.buffer.read(length))


def _write_message(message: dict) -> None:
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
    sys.stdout.buffer.flush()


def main() -> int:
    while message := _read_message():
        if message.get("method") == "initialize":
            _write_message({"jsonrpc": "2.0", "id": message["id"], "result": {"capabilities": {}}})
        elif message.get("method") == "shutdown":
            _write_message({"jsonrpc": "2.0", "id": message["id"], "result": None})
        elif message.get("method") == "exit":
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
