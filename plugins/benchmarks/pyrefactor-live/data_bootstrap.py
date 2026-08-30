"""Provision the repositories this benchmark's tasks are pinned to.

Tasks reference a commit in a public repository; the platform exports that
commit's tree from a bare mirror, so the mirror has to exist before a run
starts. Network access happens here, never at task time.

The mirror path is derived the same way the platform derives it — a SHA-1 of
the clone URL under the shared mirrors directory — because plugins cannot
import server code.

Adding a project: add tasks to tasks.yaml; the clone URLs and pinned commits
are read from there.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import yaml

TASKS_FILE = Path(__file__).with_name("tasks.yaml")


def mirror_dir(mirrors_root: Path, url: str) -> Path:
    return mirrors_root / f"{hashlib.sha1(url.encode()).hexdigest()}.git"


def _mirrors_root() -> Path:
    return Path(os.getenv("RP_DATA_DIR",
                          str(Path.home() / "refactor-platform" / "data"))) / "mirrors"


def _repositories() -> dict[str, set[str]]:
    """Clone URL -> the commits tasks pin, read from tasks.yaml itself.

    A task whose commit is missing from the mirror would fail at run time with
    an unhelpful export error, so the pins are the source of truth here.
    """
    document = yaml.safe_load(TASKS_FILE.read_text(encoding="utf-8")) or {}
    pins: dict[str, set[str]] = {}
    for task in document.get("tasks", []):
        workspace = task.get("workspace") or {}
        if workspace.get("type") != "git":
            continue
        url = str(workspace.get("source", "")).strip()
        ref = str(workspace.get("ref", "")).strip()
        if url:
            pins.setdefault(url, set())
            if ref:
                pins[url].add(ref)
    return pins


def _is_bare_repository(path: Path) -> bool:
    if not path.is_dir():
        return False
    probe = subprocess.run(["git", "--git-dir", str(path), "rev-parse", "--is-bare-repository"],
                           capture_output=True, text=True)
    return probe.returncode == 0 and probe.stdout.strip() == "true"


def _has_commit(mirror: Path, ref: str) -> bool:
    probe = subprocess.run(["git", "--git-dir", str(mirror), "cat-file", "-e", f"{ref}^{{commit}}"],
                           capture_output=True, text=True)
    return probe.returncode == 0


def _ensure_mirror(mirrors_root: Path, url: str, refs: set[str]) -> Path:
    dest = mirror_dir(mirrors_root, url)
    if not _is_bare_repository(dest):
        if dest.exists():
            subprocess.run(["rm", "-rf", str(dest)], check=True)
        print(f"Cloning {url}", flush=True)
        subprocess.run(["git", "clone", "--mirror", url, str(dest)], check=True)
    missing = [ref for ref in sorted(refs) if not _has_commit(dest, ref)]
    if missing:
        print(f"Fetching {len(missing)} pinned commit(s) for {url}", flush=True)
        subprocess.run(["git", "--git-dir", str(dest), "fetch", "--tags", "--force", "origin",
                        "+refs/heads/*:refs/heads/*"], check=True)
    still_missing = [ref for ref in sorted(refs) if not _has_commit(dest, ref)]
    if still_missing:
        raise RuntimeError(f"{url} does not contain pinned commit(s): {', '.join(still_missing)}")
    return dest


def bootstrap(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    mirrors_root = _mirrors_root()
    mirrors_root.mkdir(parents=True, exist_ok=True)
    repositories = _repositories()
    for index, (url, refs) in enumerate(sorted(repositories.items()), start=1):
        print(f"Provisioning repository {index}/{len(repositories)}: {url}", flush=True)
        _ensure_mirror(mirrors_root, url, refs)


if __name__ == "__main__":
    bootstrap(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data")
