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
import stat
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
        # Owning the leaf is insufficient when a volume or test harness created
        # an ancestor as root with mode 0700. Python's UID-drop path handling
        # in the container requires read+traverse (execute alone returns EACCES).
        # Do not change ownership or write permissions of shared data.
        for parent in p.parents:
            if parent == Path("/"):
                break
            try:
                mode = parent.stat().st_mode
                required = stat.S_IROTH | stat.S_IXOTH
                if mode & required != required:
                    parent.chmod(mode | required)
            except OSError:
                break


def demote_kwargs(pw: pwd.struct_passwd | None) -> dict:
    """subprocess kwargs that drop privileges; empty when not needed."""
    if pw is None:
        return {}
    return {
        "user": pw.pw_uid,
        "group": pw.pw_gid,
        # Never inherit root's supplementary groups. Besides being a privilege
        # leak, group 0 makes restrictive group bits override otherwise-valid
        # "other" traverse permissions on root-owned volumes.
        "extra_groups": [],
    }
