"""One unprivileged identity for everything that touches a task's files.

The agent session and the evaluation build must run as the *same* user. When
the agent ran as root it left root-owned scratch under shared paths (`/tmp`),
which the unprivileged build could then not delete — surfacing as phantom test
errors that looked like the agent's fault.

Running as root at all also breaks suites that assert on permission denial:
root bypasses `chmod`. Hence: demote both.
"""
from __future__ import annotations

import os
import pwd
import subprocess
from pathlib import Path


def build_user() -> pwd.struct_passwd | None:
    """The unprivileged user to run as, or None when already unprivileged
    (or the user does not exist — e.g. a bare `uv run` dev box)."""
    if os.geteuid() != 0:
        return None
    try:
        return pwd.getpwnam(os.getenv("RP_BUILD_USER", "runner"))
    except KeyError:
        return None


def chown_tree(pw: pwd.struct_passwd, *paths: str | Path) -> None:
    for path in paths:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        subprocess.run(["chown", "-R", f"{pw.pw_uid}:{pw.pw_gid}", str(p)], check=False)


def demote_kwargs(pw: pwd.struct_passwd | None) -> dict:
    """subprocess kwargs that drop privileges; empty when not needed."""
    return {"user": pw.pw_uid, "group": pw.pw_gid} if pw else {}
