"""Own the agent process under a PTY. Every byte is appended once to
terminal.log (live stream source + replay source). Completion = process exit;
timeout = kill the process group. No tmux, no exit-code markers.
"""
from __future__ import annotations

import asyncio
import fcntl
import os
import pty
import signal
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.catalog.sdk import CommandSpec

_TIOCSWINSZ = 0x5414  # asm-generic; matches Linux x86_64/arm64


@dataclass
class PtyResult:
    exit_code: int | None
    timed_out: bool
    pid: int
    interrupted: bool = False


def _set_winsize(fd: int, rows: int = 50, cols: int = 200) -> None:
    fcntl.ioctl(fd, _TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


async def run_pty(
    cmd: CommandSpec,
    terminal_log: Path,
    on_bytes: Callable[[bytes], None],
    timeout: float,
    on_pid: Callable[[int], None] | None = None,
    should_kill: Callable[[], bool] | None = None,
    run_as: dict | None = None,
) -> PtyResult:
    terminal_log.parent.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _run_blocking, cmd, terminal_log, on_bytes, timeout, on_pid, should_kill, run_as
    )


def _run_blocking(cmd, terminal_log, on_bytes, timeout, on_pid, should_kill, run_as=None) -> PtyResult:
    master, slave = pty.openpty()
    _set_winsize(master)
    env = dict(os.environ)
    env.update(cmd.env)
    if run_as:
        # The agent shells out (mvn, pytest, …); it must share the build's
        # identity or it leaves scratch the build cannot clean up.
        os.fchown(slave, run_as["user"], run_as["group"])
    proc = subprocess.Popen(
        cmd.argv, stdin=slave, stdout=slave, stderr=slave,
        cwd=str(cmd.cwd), env=env, start_new_session=True,
        **(run_as or {}),
    )
    os.close(slave)
    if on_pid:
        on_pid(proc.pid)
    os.set_blocking(master, False)
    timed_out = False
    import time
    interrupted = False
    end = time.monotonic() + timeout if timeout and timeout > 0 else None
    with terminal_log.open("wb") as log:
        while True:
            if proc.poll() is not None:
                _drain(master, log, on_bytes)
                break
            if end is not None and time.monotonic() > end:
                timed_out = True
                _killpg(proc.pid)
                _drain(master, log, on_bytes)
                break
            if should_kill is not None and should_kill():
                interrupted = True
                _killpg(proc.pid)
                _drain(master, log, on_bytes)
                break
            try:
                chunk = os.read(master, 65536)
                if chunk:
                    log.write(chunk)
                    log.flush()
                    on_bytes(chunk)
            except (BlockingIOError, OSError):
                time.sleep(0.03)
    os.close(master)
    exit_code = proc.wait()
    return PtyResult(exit_code=exit_code, timed_out=timed_out, pid=proc.pid,
                     interrupted=interrupted)


def _drain(master: int, log, on_bytes) -> None:
    try:
        while True:
            chunk = os.read(master, 65536)
            if not chunk:
                break
            log.write(chunk)
            on_bytes(chunk)
    except OSError:
        pass


def _killpg(pid: int) -> None:
    import time
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        return
    for _ in range(50):
        try:
            os.killpg(pid, 0)
        except OSError:
            return
        time.sleep(0.1)
    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        pass


def kill_pid_group(pid: int) -> None:
    _killpg(pid)
