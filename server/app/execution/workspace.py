"""Per-task isolated workspaces. Both providers end identically: a plain tree
with a fresh git baseline (no upstream history — solution commits must be
unreachable from the agent's workspace).
"""
from __future__ import annotations

import asyncio
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.catalog.sdk import TaskDef

_GIT_ENV = {"GIT_AUTHOR_NAME": "platform", "GIT_AUTHOR_EMAIL": "platform@local",
            "GIT_COMMITTER_NAME": "platform", "GIT_COMMITTER_EMAIL": "platform@local",
            # The agent owns the workspace (unprivileged user); the platform
            # inspects it as root. Without this git aborts on "dubious ownership".
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": "*"}


def mirror_path(mirrors_root: Path, source: str) -> Path:
    return mirrors_root / f"{hashlib.sha1(source.encode()).hexdigest()}.git"


def _run(args: list[str], cwd: Path | None = None,
         extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    import os
    env = {**os.environ, **_GIT_ENV, **(extra_env or {})}
    return subprocess.run(args, cwd=str(cwd) if cwd else None, env=env,
                          capture_output=True, text=True, check=True)


def _prepare_sync(task: TaskDef, dest: Path, data_root: Path, mirrors_root: Path) -> str:
    dest.mkdir(parents=True, exist_ok=True)
    ws = task.workspace
    if ws.type == "snapshot":
        src = data_root / ws.source
        shutil.copytree(src, dest, dirs_exist_ok=True)
    elif ws.type == "git":
        mirror = mirror_path(mirrors_root, ws.source)
        if not mirror.exists():
            raise FileNotFoundError(f"mirror missing for {ws.source}; run data bootstrap")
        ref = ws.ref or "HEAD"
        # export the tree at the pinned ref without carrying history
        proc = subprocess.Popen(["git", "-C", str(mirror), "archive", ref],
                                stdout=subprocess.PIPE)
        subprocess.run(["tar", "-x", "-C", str(dest)], stdin=proc.stdout, check=True)
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"git archive failed for {ws.source}@{ref}")
    else:
        raise ValueError(f"unknown workspace type: {ws.type}")

    _run(["git", "init", "-q"], cwd=dest)
    _run(["git", "add", "-A"], cwd=dest)
    _run(["git", "commit", "-q", "-m", "baseline", "--allow-empty"], cwd=dest)
    return _run(["git", "rev-parse", "HEAD"], cwd=dest).stdout.strip()


async def prepare(task: TaskDef, dest: Path, data_root: Path, mirrors_root: Path) -> str:
    return await asyncio.get_running_loop().run_in_executor(
        None, _prepare_sync, task, dest, data_root, mirrors_root)


def capture_diff(dest: Path) -> str:
    """Authoritative code delta, including untracked files."""
    _run(["git", "add", "-A"], cwd=dest)
    out = _run(["git", "diff", "--cached", "HEAD"], cwd=dest).stdout
    return out


def changed_files(dest: Path) -> list[str]:
    _run(["git", "add", "-A"], cwd=dest)
    out = _run(["git", "diff", "--cached", "--name-only", "HEAD"], cwd=dest).stdout
    return [line for line in out.splitlines() if line.strip()]


def live_diff(dest: Path) -> str:
    """The same delta as capture_diff(), computed without touching the agent's
    index: `git add -A` is staged into a throwaway GIT_INDEX_FILE. Safe to poll
    while the agent is still editing the workspace."""
    with tempfile.TemporaryDirectory(prefix="rp-index-") as tmp:
        env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
        _run(["git", "read-tree", "HEAD"], cwd=dest, extra_env=env)
        _run(["git", "add", "-A"], cwd=dest, extra_env=env)
        return _run(["git", "diff", "--cached", "HEAD"], cwd=dest, extra_env=env).stdout


def ignore_paths(dest: Path, paths: list[str]) -> None:
    """Keep platform-injected scaffolding (eval.sh, LSP config, …) out of the
    agent's diff. These land after the baseline commit, so `git add -A` would
    otherwise sweep them in and `workspace_changed` would pass on them alone."""
    if not paths:
        return
    exclude = dest / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    new = [p for p in paths if p not in existing.splitlines()]
    if new:
        with exclude.open("a", encoding="utf-8") as fh:
            fh.write("\n# platform-injected, not part of the agent's change\n")
            fh.write("\n".join(new) + "\n")


def status_files(dest: Path) -> list[dict[str, str]]:
    """Read-only working-tree status. Safe to poll while the agent is editing —
    unlike changed_files(), which stages everything with `git add -A`."""
    out = _run(["git", "status", "--porcelain", "-uall"], cwd=dest).stdout
    entries = []
    for line in out.splitlines():
        if len(line) > 3:
            entries.append({"status": line[:2].strip() or "?", "path": line[3:].strip()})
    return entries


def head_sha(dest: Path) -> str:
    return _run(["git", "rev-parse", "HEAD"], cwd=dest).stdout.strip()
