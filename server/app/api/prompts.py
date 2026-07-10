"""Operator-editable prompt templates.

A benchmark ships default templates in its plugin directory. Edits are stored as
overrides in the data volume (so they survive image rebuilds) and take
precedence at prompt-build time. Reset deletes the override, restoring the
shipped default.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(prefix="/api")

_SUFFIXES = (".txt", ".j2", ".md", ".md.j2")


class PromptBody(BaseModel):
    content: str


def _plugin_prompts_dir(request: Request, benchmark: str) -> Path:
    loaded = request.app.state.registry.benchmarks.get(benchmark)
    if loaded is None:
        raise HTTPException(404, f"unknown benchmark: {benchmark}")
    return loaded.plugin_dir / "prompts"


def override_dir(benchmark: str) -> Path:
    return get_settings().prompt_overrides_dir / benchmark


def _safe(base: Path, name: str) -> Path:
    """Templates are addressed by name; refuse anything that escapes the dir."""
    target = (base / name).resolve()
    if base.resolve() not in target.parents and target.parent != base.resolve():
        raise HTTPException(400, "invalid template name")
    if not name.endswith(_SUFFIXES):
        raise HTTPException(400, "unsupported template type")
    return target


@router.get("/prompts/{benchmark}")
def list_prompts(benchmark: str, request: Request):
    shipped = _plugin_prompts_dir(request, benchmark)
    over = override_dir(benchmark)
    names = sorted({p.name for p in shipped.glob("*") if p.is_file()} |
                   {p.name for p in over.glob("*") if p.is_file()} if shipped.is_dir() or over.is_dir() else set())
    return {
        "benchmark": benchmark,
        "prompts": [{"name": n, "overridden": (over / n).is_file()} for n in names],
    }


@router.get("/prompts/{benchmark}/{name}")
def get_prompt(benchmark: str, name: str, request: Request):
    shipped = _safe(_plugin_prompts_dir(request, benchmark), name)
    custom = _safe(override_dir(benchmark), name)
    path = custom if custom.is_file() else shipped
    if not path.is_file():
        raise HTTPException(404, "unknown template")
    return {
        "name": name,
        "overridden": custom.is_file(),
        "content": path.read_text(encoding="utf-8"),
        "default": shipped.read_text(encoding="utf-8") if shipped.is_file() else "",
    }


@router.put("/prompts/{benchmark}/{name}")
def put_prompt(benchmark: str, name: str, body: PromptBody, request: Request):
    _plugin_prompts_dir(request, benchmark)  # validates the benchmark exists
    if not body.content.strip():
        raise HTTPException(422, "template must not be empty")
    custom = _safe(override_dir(benchmark), name)
    custom.parent.mkdir(parents=True, exist_ok=True)
    custom.write_text(body.content, encoding="utf-8")
    return {"name": name, "overridden": True}


@router.delete("/prompts/{benchmark}/{name}")
def reset_prompt(benchmark: str, name: str, request: Request):
    _plugin_prompts_dir(request, benchmark)
    custom = _safe(override_dir(benchmark), name)
    custom.unlink(missing_ok=True)
    return {"name": name, "overridden": False}
