"""Reaching the subprocesses a task starts before its agent does.

Stop used to kill one pid: the agent's terminal. Everything that runs before the
agent — exporting the checkout, the Java baseline build, indexing for retrieval,
probing a language server — had no pid registered, so pressing Stop during those
minutes did nothing and the work continued to completion.

Those children are started with `start_new_session=True`, which makes each one a
session leader: its pid equals its process-group id. That is the property used
here to find them and kill whole groups, so a build's compiler and test JVMs go
with the shell that spawned them.
"""
from __future__ import annotations

import os
from pathlib import Path

_PROC = Path("/proc")


def direct_children(pid: int | None = None) -> set[int]:
    """Pids of the immediate children of `pid` (this process by default)."""
    pid = os.getpid() if pid is None else pid
    found: set[int] = set()
    task_dir = _PROC / str(pid) / "task"
    try:
        threads = list(task_dir.iterdir())
    except OSError:
        return found
    for thread in threads:
        try:
            listed = (thread / "children").read_text()
        except OSError:
            continue
        for word in listed.split():
            if word.isdigit():
                found.add(int(word))
    return found


def _is_session_leader(pid: int) -> bool:
    try:
        return os.getpgid(pid) == pid
    except (ProcessLookupError, PermissionError, OSError):
        return False


def kill_child_groups(exclude: set[int] | None = None) -> list[int]:
    """Kill the process group of every session-leading child of this process.

    `exclude` keeps a pid this caller is managing itself, such as the agent's
    terminal. Returns the group leaders that were signalled.
    """
    import signal

    skip = exclude or set()
    killed: list[int] = []
    for pid in direct_children():
        if pid in skip or not _is_session_leader(pid):
            continue
        try:
            os.killpg(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            continue
        killed.append(pid)
    return killed
