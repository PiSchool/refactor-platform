"""Run one command against a task's workspace, on the platform's terms.

A metric decides what to run and how to read the output. Everything around that
is the platform's: which identity owns the files, that the command gets its own
process group, and that a timeout kills the whole tree rather than the shell at
the top of it.

That last point was a real failure: a Gradle build whose shell was killed on
timeout left its JVMs compiling, one deployment held a daemon 54 minutes after
its task had ended, and the tasks queued behind it competed for the same CPU.

Re-exported by `app.catalog.sdk`, which is the only module a plugin imports.
"""
from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class CommandOutcome:
    """What one command did: succeeded, what it printed, and how it ended."""

    ok: bool
    output: str
    timed_out: bool = False
    returncode: int | None = None


def run_in_workspace(
    workspace: Path,
    command: str | Sequence[str],
    *,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
    writable: Sequence[str | Path] = (),
    demote: bool = True,
) -> CommandOutcome:
    """Run `command` in `workspace` and return what it did.

    `command` is a shell line when it is a string and an argv when it is a
    sequence. `writable` names paths outside the workspace the command must be
    able to write, such as a build tool's local repository. `demote` runs the
    command as the same unprivileged user that owned the agent session, which is
    required for any suite that asserts on permission denial: root bypasses
    `chmod` and such a suite passes where it should fail.
    """
    full_env = {**os.environ, **(env or {})}
    # Suites compare accented text; an unset locale gives Java an ASCII default
    # charset (ANSI_X3.4-1968) and they fail on an unmodified checkout.
    full_env.setdefault("LANG", "C.UTF-8")
    full_env.setdefault("LC_ALL", "C.UTF-8")

    kwargs: dict = {}
    if demote:
        kwargs = _demote(workspace, writable, full_env)
    kwargs.setdefault("start_new_session", True)

    try:
        proc = subprocess.Popen(
            command,
            shell=isinstance(command, str),
            cwd=str(workspace),
            env=full_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs,
        )
    except FileNotFoundError as exc:
        return CommandOutcome(ok=False, output=str(exc))

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _kill_tree(proc)
        stdout, stderr = proc.communicate()
        return CommandOutcome(
            ok=False,
            output=_timeout_output(exc) + (stdout or "") + (stderr or ""),
            timed_out=True,
            returncode=proc.returncode,
        )
    return CommandOutcome(
        ok=proc.returncode == 0,
        output=(stdout or "") + (stderr or ""),
        returncode=proc.returncode,
    )


def _demote(workspace: Path, writable: Sequence[str | Path], env: dict[str, str]) -> dict:
    """Subprocess arguments that run as the shared unprivileged user.

    Imported here rather than at module scope so the plugin surface does not pull
    in the execution package.
    """
    from app.execution.sandbox import build_user, chown_tree, demote_kwargs

    pw = build_user()
    if pw is None:
        return {}
    chown_tree(pw, workspace, *writable, pw.pw_dir)
    # HOME must be writable by that user or Maven and Gradle cannot create their
    # caches, and the build fails for a reason that has nothing to do with code.
    env["HOME"] = pw.pw_dir
    return demote_kwargs(pw)


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        proc.kill()


def _timeout_output(exc: subprocess.TimeoutExpired) -> str:
    def text(value) -> str:
        if value is None:
            return ""
        return value.decode(errors="replace") if isinstance(value, bytes) else str(value)

    return text(exc.stdout or exc.output) + text(exc.stderr)
