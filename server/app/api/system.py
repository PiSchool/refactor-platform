from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app import build_info
from app.catalog import tools
from app.retrieval.health import retrieval_rows, status as retrieval_status


router = APIRouter(prefix="/api")


def _probe(binary: str, argument: str = "--version") -> str:
    return tools.probe_version(binary, argument) or "absent"


@router.get("/health")
async def health(request: Request):
    worker = getattr(request.app.state, "worker", None)
    retrieval = await asyncio.to_thread(retrieval_status, True)
    readiness: dict = {"ready": True}
    status_code = 200

    if worker is None:
        status_code = 503
        readiness = {
            "ready": False,
            "code": "worker_unavailable",
            "detail": "The run worker is not running.",
        }
    elif retrieval.get("status") == "error":
        status_code = 503
        readiness = {
            "ready": False,
            "code": "retrieval_unavailable",
            "detail": "The required S2 retrieval service is unavailable.",
        }

    payload = {
        "status": "ok" if status_code == 200 else "unhealthy",
        "db": "ok",
        "worker": "running" if worker is not None else "unhealthy",
        "readiness": readiness,
        "retrieval": retrieval,
        # What this container was built from, so a redeploy can be verified
        # without reading the dashboard for behavioural differences.
        "build": build_info.report(),
    }
    if status_code != 200:
        return JSONResponse(status_code=status_code, content=payload)
    return payload


#: What the platform itself needs, and what stops working without it. Every
#: plugin-supplied command — agent CLIs, language servers — is reported with its
#: plugin in Settings, so that it is stated once.
_TOOLCHAIN = (
    ("Java", "java", "-version", "benchmarks in Java"),
    ("Maven", "mvn", "--version", "Java projects built with Maven"),
    ("Gradle", "gradle", "--version", "Java projects built with Gradle"),
    ("Python", "python3", "--version", "benchmarks in Python"),
    ("Node.js", "node", "--version", "the dashboard"),
    ("Git", "git", "--version", "every task workspace"),
)
_TTL_SECONDS = 300
_cache: dict = {"at": 0.0, "value": None}


def _row(name: str, value: str, needed_by: str = "", install: str = "", detail: str = "") -> dict:
    return {
        "name": name,
        "value": value,
        "state": "absent" if value == "absent" else "ok",
        "neededBy": needed_by,
        "install": install,
        "detail": detail,
    }


def _deployment_rows() -> list[dict]:
    """Identity of the running backend. The dashboard appends its own row."""
    info = build_info.report()
    built = f"built {info['builtAt']}" if info["builtAt"] else "built outside an image build"
    rows = [_row("Backend", info["fingerprint"], detail=f"source fingerprint · {built}")]
    if info["revision"]:
        rows.append(_row("Revision", info["revision"],
                         detail="recorded when the images were built"))
    return rows


@router.get("/system")
def system(request: Request, refresh: bool = False):
    """What this deployment can run, grouped by what an operator would ask about.

    `def`, not `async def`: each probe spawns a process (gradle boots a JVM),
    which would otherwise stall the event loop. Cached, because Settings polls it.
    """
    if _cache["value"] and not refresh and time.time() - _cache["at"] < _TTL_SECONDS:
        return _cache["value"]
    if refresh:
        tools.forget()
    value = {"groups": [
        {
            "key": "deployment",
            "title": "Deployment",
            "detail": ("What each container was built from. A rebuild that changed something "
                       "changes these values; scripts/deployment_status.py compares them "
                       "with the working tree."),
            "rows": _deployment_rows(),
        },
        {
            "key": "toolchain",
            "title": "Build and language toolchain",
            "detail": "Probed inside this container, where evaluation runs.",
            "rows": [_row(name, _probe(binary, argument), needed)
                     for name, binary, argument, needed in _TOOLCHAIN],
        },
        {
            "key": "retrieval",
            "title": "Retrieval",
            "detail": ("Every stage an S2 query passes through, with the model and the "
                       "candidate count it uses."),
            "rows": retrieval_rows(),
        },
    ]}
    _cache.update(at=time.time(), value=value)
    return value
