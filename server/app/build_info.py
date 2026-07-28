"""What the running deployment was built from.

A rebuilt container is otherwise indistinguishable from the one it replaced: the
dashboard looks the same and the API answers the same shapes, so an operator who
redeployed has no way to tell whether the image carries their changes. Each
component therefore reports an identity, and the platform surfaces it on
`/api/health` and in Settings → Services.

`fingerprint` hashes the source whose content decides how the backend behaves:
the server package, the plugins directory, and `config.yaml`. Benchmark data,
caches and test suites are excluded — they ship in the image but do not change
what a run does. The same function over a working tree yields the same value,
which is what `scripts/deployment_status.py` compares.

`stamp` reports the revision and build time recorded when the image was built.
Both are empty for a build that was not stamped (a checkout started with
uvicorn, or `docker compose build` without `RP_BUILD_REV`); the fingerprint is
then reported alone rather than inventing a version.
"""
from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path

#: Path to the `key=value` file written by docker/backend.Dockerfile.
STAMP_PATH_ENV = "RP_BUILD_STAMP"

#: Directory names that never affect behaviour: caches, dependencies, benchmark
#: data bootstrapped into a volume, and tests.
SKIP_DIRS = frozenset({
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".venv", "node_modules", "data", "tests",
})
SKIP_SUFFIXES = (".pyc", ".pyo")
#: `.ready` marks a provisioned benchmark; it appears after the image is built.
SKIP_NAMES = frozenset({".ready", ".DS_Store"})


def _include(relative: Path) -> bool:
    if SKIP_DIRS.intersection(relative.parts):
        return False
    return relative.name not in SKIP_NAMES and relative.suffix not in SKIP_SUFFIXES


def _absorb_tree(digest, root: Path, label: str) -> None:
    """Hash every file under `root` under a stable label.

    The label makes the value comparable between an image, where the server
    package sits at /app/server/app, and a checkout, where it sits at
    server/app.
    """
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not _include(relative) or not path.is_file():
            continue
        digest.update(f"{label}/{relative.as_posix()}\0".encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())


def fingerprint(*, server_package: Path, plugins_dir: Path, config: Path | None) -> str:
    digest = hashlib.sha256()
    _absorb_tree(digest, server_package, "server/app")
    _absorb_tree(digest, plugins_dir, "plugins")
    if config is not None and config.is_file():
        digest.update(b"config.yaml\0")
        digest.update(hashlib.sha256(config.read_bytes()).digest())
    return digest.hexdigest()[:12]


@lru_cache(maxsize=1)
def running_fingerprint() -> str:
    """Fingerprint of the code this process is executing.

    Cached: the source of a running container does not change, and `/api/health`
    is polled.
    """
    from app.config import config_file, get_settings

    return fingerprint(
        server_package=Path(__file__).resolve().parent,
        plugins_dir=get_settings().plugins_dir,
        config=config_file(),
    )


def tree_fingerprint(repo_root: Path) -> str:
    """Fingerprint of a checkout, for comparison against a running deployment."""
    return fingerprint(
        server_package=repo_root / "server" / "app",
        plugins_dir=repo_root / "plugins",
        config=repo_root / "config.yaml",
    )


def stamp() -> dict[str, str]:
    values = {"revision": "", "builtAt": ""}
    path = os.getenv(STAMP_PATH_ENV, "").strip()
    if path and Path(path).is_file():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() in values:
                values[key.strip()] = value.strip()
    # An explicit variable wins, so a deployment that runs the code outside an
    # image build can still declare what it is serving.
    for key, env_name in (("revision", "RP_BUILD_REV"), ("builtAt", "RP_BUILD_TIME")):
        override = os.getenv(env_name, "").strip()
        if override:
            values[key] = override
    return values


def report() -> dict[str, str]:
    """Identity of the running backend."""
    return {**stamp(), "fingerprint": running_fingerprint()}
