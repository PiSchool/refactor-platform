#!/usr/bin/env python3
"""Is the running deployment the code in this working tree?

A container that was not replaced looks exactly like one that was, so after
`docker compose up -d --build` there is nothing on screen to confirm the rebuild
took effect. This compares what each component reports about itself with a
fingerprint of the source on disk.

    python3 scripts/deployment_status.py
    python3 scripts/deployment_status.py --url http://127.0.0.1:8787

Exit status is 0 when every component matches the working tree, 1 otherwise, so
it can gate a deployment step.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "server"))

from app import build_info  # noqa: E402  (needs the path above)


def default_url() -> str:
    """The dashboard origin, which also proxies the API."""
    port = os.getenv("RP_WEB_PORT", "").strip()
    if not port:
        env_file = REPO_ROOT / ".env"
        if env_file.is_file():
            for raw in env_file.read_text(encoding="utf-8").splitlines():
                key, separator, value = raw.partition("=")
                if separator and key.strip() == "RP_WEB_PORT":
                    port = value.strip()
    return f"http://127.0.0.1:{port or '3000'}"


def fetch(url: str, timeout: float = 10.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return None


def dashboard_tree_fingerprint() -> str:
    """The same fingerprint the dashboard image records, over the working tree."""
    script = REPO_ROOT / "web" / "scripts" / "build-fingerprint.mjs"
    if not script.is_file():
        return ""
    try:
        done = subprocess.run(
            ["node", str(script)], cwd=REPO_ROOT / "web",
            capture_output=True, text=True, timeout=120, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def line(component: str, running: str, tree: str) -> tuple[str, bool]:
    """One report row, and whether it counts as up to date."""
    if not running:
        return f"{component:<10} {'not reporting':<14} {tree or 'n/a':<14} unreachable, or an older build", False
    if not tree:
        return f"{component:<10} {running:<14} {'not computed':<14} the working tree could not be fingerprinted", True
    verdict = "matches the working tree" if running == tree else "STALE — rebuild required"
    return f"{component:<10} {running:<14} {tree:<14} {verdict}", running == tree


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=default_url(),
                        help="dashboard origin (default: %(default)s)")
    args = parser.parse_args()
    url = args.url.rstrip("/")

    health = fetch(f"{url}/api/health") or fetch("http://127.0.0.1:8000/api/health") or {}
    dashboard = fetch(f"{url}/rp-build") or {}
    backend_build = health.get("build") or {}

    print(f"{url}\n")
    print(f"{'component':<10} {'running':<14} {'working tree':<14} verdict")
    rows = [
        line("backend", backend_build.get("fingerprint", ""),
             build_info.tree_fingerprint(REPO_ROOT)),
        line("dashboard", dashboard.get("fingerprint", ""), dashboard_tree_fingerprint()),
    ]
    for text, _ in rows:
        print(text)

    stamped = {name: value for name, value in (
        ("revision", backend_build.get("revision", "")),
        ("built", backend_build.get("builtAt", "")),
    ) if value}
    if stamped:
        print("\n" + "  ".join(f"{name} {value}" for name, value in stamped.items()))
    else:
        print("\nno revision recorded: export RP_BUILD_REV before building to stamp one")

    if all(ok for _, ok in rows):
        return 0
    print("\nrebuild and restart:  docker compose up -d --build")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
