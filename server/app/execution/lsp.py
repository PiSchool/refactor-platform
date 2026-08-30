"""Language-server readiness checks using the LSP initialize handshake."""
from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


def _frame(message: dict[str, Any]) -> bytes:
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _messages(buffer: bytearray):
    while True:
        header_end = buffer.find(b"\r\n\r\n")
        separator_size = 4
        if header_end < 0:
            header_end = buffer.find(b"\n\n")
            separator_size = 2
        if header_end < 0:
            return
        header = bytes(buffer[:header_end]).decode("ascii", errors="replace")
        length = None
        for line in header.splitlines():
            name, _, value = line.partition(":")
            if name.strip().lower() == "content-length":
                try:
                    length = int(value.strip())
                except ValueError:
                    length = None
                break
        if length is None:
            del buffer[:header_end + separator_size]
            continue
        body_start = header_end + separator_size
        if len(buffer) < body_start + length:
            return
        body = bytes(buffer[body_start:body_start + length])
        del buffer[:body_start + length]
        try:
            yield json.loads(body)
        except json.JSONDecodeError:
            continue


def probe_server(
    config: dict[str, Any], workspace: Path, *, timeout: float = 20.0,
    run_as: dict[str, Any] | None = None, env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """Start a server and require a valid response to LSP `initialize`.

    Finding an executable on PATH is insufficient: broken JDKs, invalid server
    arguments, and corrupt installations all pass that check and silently turn
    an S1-LSP run into S1.
    """
    command = str(config.get("command", "")).strip()
    args = [str(arg) for arg in (config.get("args") or [])]
    if not command:
        return False, "language-server config has no command"
    workspace = workspace.resolve()
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "processId": os.getpid(),
            "rootUri": workspace.as_uri(),
            "workspaceFolders": [{"uri": workspace.as_uri(), "name": workspace.name}],
            "capabilities": {},
            "clientInfo": {"name": "refactor-platform-readiness", "version": "1"},
        },
    }
    with tempfile.TemporaryFile() as stderr:
        process_env = dict(os.environ)
        process_env.update({str(k): str(v) for k, v in (config.get("env") or {}).items()})
        process_env.update(env or {})
        try:
            process = subprocess.Popen(
                [command, *args], cwd=workspace, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=stderr, start_new_session=True,
                env=process_env, **(run_as or {}),
            )
        except OSError as exc:
            return False, f"language server failed to start: {exc}"
        try:
            assert process.stdin is not None and process.stdout is not None
            try:
                process.stdin.write(_frame(request))
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                process.wait(timeout=2)
                stderr.seek(0)
                detail = stderr.read(2000).decode("utf-8", errors="replace").strip()
                return False, detail or f"language server exited with {process.returncode}"
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                buffer = bytearray()
                deadline = time.monotonic() + max(timeout, 0.1)
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        break
                    remaining = max(0.0, deadline - time.monotonic())
                    if not selector.select(min(remaining, 0.25)):
                        continue
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    for message in _messages(buffer):
                        if message.get("id") != 1:
                            continue
                        if "error" in message:
                            return False, f"LSP initialize rejected: {message['error']}"
                        if "result" in message:
                            return True, "LSP initialize handshake succeeded"
            stderr.seek(0)
            detail = stderr.read(2000).decode("utf-8", errors="replace").strip()
            if process.poll() is not None:
                return False, detail or f"language server exited with {process.returncode}"
            return False, detail or f"LSP initialize timed out after {timeout:g}s"
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except OSError:
                    pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except OSError:
                        pass
                    process.wait(timeout=2)
