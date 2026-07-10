"""Model catalog for the run wizard.

The agent runs BYOK against an OpenAI-compatible endpoint, so the set of usable
models is whatever the provider serves — not a list the platform hardcodes. We
fetch it once, cache it, and degrade gracefully when offline (the wizard still
accepts a free-text model id).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/api")

_TTL_SECONDS = 3600
_cache: dict = {"at": 0.0, "models": []}


def _is_free(model: dict) -> bool:
    pricing = model.get("pricing") or {}
    return all(float(pricing.get(k, 0) or 0) == 0 for k in ("prompt", "completion"))


def _can_drive_an_agent(model: dict) -> bool:
    """A coding agent needs a model that emits text and can call tools.

    The provider also serves image, audio and embedding models; offering those
    in the wizard lets someone launch a run that cannot possibly work (a music
    model was picked once, and the platform dutifully ran it).
    """
    architecture = model.get("architecture") or {}
    outputs = architecture.get("output_modalities") or []
    return "tools" in (model.get("supported_parameters") or []) and "text" in outputs


def _fetch(base_url: str, api_key: str) -> list[dict]:
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        payload = json.load(r)
    data = payload.get("data", [])
    # Plain OpenAI-compatible endpoints publish no capability metadata; filtering
    # on it there would empty the catalog, so only filter when it exists.
    declares_capabilities = any(m.get("supported_parameters") for m in data)
    models = []
    for m in data:
        if declares_capabilities and not _can_drive_an_agent(m):
            continue
        pricing = m.get("pricing") or {}
        models.append({
            "id": m.get("id"),
            "name": m.get("name") or m.get("id"),
            "contextLength": m.get("context_length"),
            "free": _is_free(m),
            # USD per token, straight from the provider
            "pricing": {k: pricing[k] for k in
                        ("prompt", "completion", "input_cache_read", "input_cache_write")
                        if k in pricing},
        })
    return sorted((m for m in models if m["id"]), key=lambda m: (not m["free"], m["id"]))


def model_index() -> dict[str, dict]:
    """id → model, from the cache. Empty when the catalog was never fetched."""
    return {m["id"]: m for m in _cache["models"]}


def ensure_catalog() -> dict[str, dict]:
    """Fetch the catalog if it is not cached yet; never raise."""
    if not _cache["models"]:
        try:
            list_models()
        except Exception:
            pass
    return model_index()


@router.get("/models")
def list_models(refresh: bool = False):
    """Provider model catalog. `source` tells the UI whether this is live."""
    settings = get_settings()
    base_url, api_key = settings.provider_base_url(), settings.provider_api_key()

    fresh = time.time() - _cache["at"] < _TTL_SECONDS
    if _cache["models"] and fresh and not refresh:
        return {"models": _cache["models"], "source": "cache"}

    if not base_url:
        return {"models": _cache["models"], "source": "unconfigured",
                "detail": "No provider base URL configured."}
    try:
        models = _fetch(base_url, api_key)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        # Offline or provider down: keep the wizard usable with free-text ids.
        return {"models": _cache["models"], "source": "error", "detail": str(exc)}

    _cache.update(at=time.time(), models=models)
    return {"models": models, "source": "provider"}
