"""What a declared command actually is on this machine.

A plugin declares the executable it drives (`binary`) and how to install it
(`install`). Whether that executable is present, and which version it is, is a
property of the deployment, not of the manifest — so it is asked once, here, and
every reader uses the answer: the plugin list in Settings, the system report, and
the provenance written beside a finished task.

The manifests used to carry a `version` of their own, which a run recorded as the
agent's version. Nothing kept it in step with the installed CLI, and an exported
run claimed a version that had not run. Asking the tool removes the possibility.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import time

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_TTL_SECONDS = 300
_cache: dict[str, tuple[float, str]] = {}

#: The version itself, wherever the tool puts it in its answer: `aider 0.86.2`,
#: `codex-cli 0.145.0`, `GitHub Copilot CLI 1.0.75.`, `1.0.75-beta.2`.
_VERSION = re.compile(r"\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.]+)?")


def _first_line(text: str) -> str:
    """The first line of substance. Some tools lead with a banner or a divider."""
    for line in _ANSI.sub("", text).splitlines():
        line = line.strip()
        if line and not set(line) <= set("-=_ "):
            return line[:120]
    return ""


def probe_version(binary: str, argument: str = "--version") -> str:
    """The version the installed `binary` reports, or an empty string.

    Cached: Settings polls, and a probe spawns a process — `gradle --version`
    boots a JVM.
    """
    if not binary:
        return ""
    hit = _cache.get(binary)
    if hit and time.time() - hit[0] < _TTL_SECONDS:
        return hit[1]
    value = ""
    if shutil.which(binary):
        try:
            out = subprocess.run([binary, argument], capture_output=True, text=True, timeout=10)
            value = _first_line(out.stdout or out.stderr) or "installed"
        except Exception:
            value = "installed"
    _cache[binary] = (time.time(), value)
    return value


def short_version(binary: str, name: str = "") -> str:
    """Just the version, beside a row that already carries the tool's name.

    `copilot --version` answers `GitHub Copilot CLI 1.0.75.` and `codex
    --version` answers `codex-cli 0.145.0`; only the number is information. When
    the answer contains no version, it is shown as the tool gave it.
    """
    reported = probe_version(binary)
    if not reported or reported == "installed":
        return reported
    found = _VERSION.search(reported)
    return found.group(0) if found else reported.rstrip(". ")


def command_state(manifest) -> dict:
    """How this deployment can run the plugin's tool.

    `bundled` is not `absent`: an adapter may drive something it ships itself, and
    calling that missing would refuse a run that would have worked.
    """
    binary = getattr(manifest, "binary", "") or ""
    if not binary:
        return {"binary": "", "state": "bundled", "version": "", "install": ""}
    if not shutil.which(binary):
        return {
            "binary": binary,
            "state": "absent",
            "version": "",
            "install": getattr(manifest, "install", "") or "",
        }
    return {
        "binary": binary,
        "state": "ok",
        "version": short_version(binary, getattr(manifest, "name", "") or ""),
        "install": "",
    }


def forget() -> None:
    """Drop the cache, so a re-probe reflects an install that just happened."""
    _cache.clear()
