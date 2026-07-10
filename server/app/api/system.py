from __future__ import annotations

import re
import shutil
import subprocess
import time

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api")


_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _probe(cmd: list[str]) -> str:
    exe = shutil.which(cmd[0])
    if not exe:
        return "absent"
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception:
        return "present"
    text = _ANSI.sub("", out.stdout or out.stderr)
    # tools like gradle lead with a banner/divider; take the first line of substance
    for line in text.splitlines():
        line = line.strip()
        if line and not set(line) <= set("-=_ "):
            return line[:120]
    return "present"


@router.get("/health")
async def health(request: Request):
    worker = getattr(request.app.state, "worker", None)
    return {"status": "ok", "db": "ok", "worker": "running" if worker else "idle"}


_PROBES = {
    "copilotCli": ["copilot", "--version"],
    "node": ["node", "--version"],
    "git": ["git", "--version"],
    "java": ["java", "-version"],
    "maven": ["mvn", "--version"],
    "gradle": ["gradle", "--version"],
}
_TTL_SECONDS = 300
_cache: dict = {"at": 0.0, "value": None}


@router.get("/system")
def system(refresh: bool = False):
    """Toolchain versions. `def`, not `async def`: each probe spawns a process
    (gradle boots a JVM), which would otherwise stall the event loop. Cached,
    because the Settings page polls this."""
    if _cache["value"] and not refresh and time.time() - _cache["at"] < _TTL_SECONDS:
        return _cache["value"]
    value = {name: _probe(cmd) for name, cmd in _PROBES.items()}
    value["pylsp"] = "present" if shutil.which("pylsp") else "absent"
    value["jdtls"] = "present" if shutil.which("jdtls") else "absent"
    _cache.update(at=time.time(), value=value)
    return value
