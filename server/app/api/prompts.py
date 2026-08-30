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

from app.catalog.sdk import PromptSpec, PromptVariable
from app.config import get_settings

router = APIRouter(prefix="/api")

#: A prompt file is named for what it is. `.j2` is a build detail of the
#: templating library and does not belong in a shipped filename.
_SUFFIXES = (".md", ".txt")

#: What the platform can say about a manifest-rendered template the benchmark
#: did not describe: it is rendered with Jinja over the task and its parameters.
#: A benchmark that declares `prompt.variables` replaces this with its own.
_MANIFEST_SPEC = PromptSpec(
    applies_to="every task in this benchmark",
    syntax="jinja",
    variables=(
        PromptVariable("task.instructions", "the task's own instruction text"),
        PromptVariable("params", "the task's parameters, as params.<key>", required=False),
    ),
)
#: A template nothing describes. Saying so beats implying a syntax it may not use.
_UNDESCRIBED = PromptSpec(applies_to="", syntax="", variables=())


class PromptBody(BaseModel):
    content: str


def _loaded(request: Request, benchmark: str):
    loaded = request.app.state.registry.benchmarks.get(benchmark)
    if loaded is None:
        raise HTTPException(404, f"unknown benchmark: {benchmark}")
    return loaded


def _plugin_prompts_dir(request: Request, benchmark: str) -> Path:
    return _loaded(request, benchmark).plugin_dir / "prompts"


def _declared(loaded) -> dict[str, PromptSpec]:
    if loaded.hooks is None:
        return {}
    try:
        return loaded.hooks.describe_prompts() or {}
    except Exception:      # a plugin defect must not make the templates unreadable
        return {}


def _from_manifest(prompt) -> PromptSpec:
    """A manifest's own declaration, falling back to what the renderer provides.

    A benchmark that ships no Python still owns its prompt contract: naming the
    values it substitutes is a list in `plugin.yaml`, not a hook.
    """
    if not getattr(prompt, "variables", None):
        return _MANIFEST_SPEC
    return PromptSpec(
        applies_to=getattr(prompt, "appliesTo", "") or _MANIFEST_SPEC.applies_to,
        syntax="jinja",   # the manifest path is rendered by the platform's Jinja
        variables=tuple(
            PromptVariable(v.name, v.summary, required=v.required) for v in prompt.variables
        ),
    )


def _spec(loaded, declared: dict[str, PromptSpec], name: str) -> PromptSpec:
    """What this template is for. A file name wins over the `"*"` entry."""
    spec = declared.get(name) or declared.get("*")
    if spec is not None:
        return spec
    prompt = getattr(loaded.manifest, "prompt", None)
    manifest_template = getattr(prompt, "template", "") or ""
    if manifest_template and Path(manifest_template).name == name:
        return _from_manifest(prompt)
    return _UNDESCRIBED


def _present(content: str, syntax: str, variable: str) -> bool:
    if syntax == "format":
        return f"{{{variable}}}" in content
    return variable in content


def _variables(content: str, spec: PromptSpec) -> list[dict]:
    return [{
        "name": v.name,
        "summary": v.summary,
        "required": v.required,
        "present": _present(content, spec.syntax, v.name),
    } for v in spec.variables]


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
    loaded = _loaded(request, benchmark)
    declared = _declared(loaded)
    return {
        "benchmark": benchmark,
        "prompts": [{
            "name": n,
            "overridden": (over / n).is_file(),
            "appliesTo": _spec(loaded, declared, n).applies_to,
            "syntax": _spec(loaded, declared, n).syntax,
        } for n in names],
    }


@router.get("/prompts/{benchmark}/{name}")
def get_prompt(benchmark: str, name: str, request: Request):
    shipped = _safe(_plugin_prompts_dir(request, benchmark), name)
    custom = _safe(override_dir(benchmark), name)
    path = custom if custom.is_file() else shipped
    if not path.is_file():
        raise HTTPException(404, "unknown template")
    loaded = _loaded(request, benchmark)
    spec = _spec(loaded, _declared(loaded), name)
    content = path.read_text(encoding="utf-8")
    return {
        "name": name,
        "overridden": custom.is_file(),
        "content": content,
        "default": shipped.read_text(encoding="utf-8") if shipped.is_file() else "",
        "appliesTo": spec.applies_to,
        "syntax": spec.syntax,
        "variables": _variables(content, spec),
    }


@router.put("/prompts/{benchmark}/{name}")
def put_prompt(benchmark: str, name: str, body: PromptBody, request: Request):
    loaded = _loaded(request, benchmark)
    if not body.content.strip():
        raise HTTPException(422, "template must not be empty")
    spec = _spec(loaded, _declared(loaded), name)
    missing = [v.name for v in spec.variables
               if v.required and not _present(body.content, spec.syntax, v.name)]
    if missing:
        # a template without them reaches the agent with the task missing from it
        raise HTTPException(
            422,
            "the benchmark substitutes these values and the template must keep them: "
            + ", ".join(missing),
        )
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
