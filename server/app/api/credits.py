"""Provider credit status for the configured BYOK key.

An exhausted key is the single most confusing failure in this platform: runs die
instantly with `provider_error`, `workspace_changed=false`, and it reads exactly
like an agent that refused to work. Surfacing the balance turns that into a
one-glance diagnosis.

Only OpenRouter publishes this (`GET /key`); every other OpenAI-compatible
endpoint returns 404, and we say "unknown" rather than inventing a number.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/api")

_TTL_SECONDS = 60
_cache: dict = {"at": 0.0, "payload": None}


def _fetch(base_url: str, api_key: str) -> dict:
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/key",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r).get("data") or {}


@router.get("/credits")
def credits(refresh: bool = False):
    """Credit limit, spend, and remainder for the configured provider key."""
    settings = get_settings()
    base_url, api_key = settings.provider_base_url(), settings.provider_api_key()

    if not (base_url and api_key):
        return {"supported": False, "detail": "No provider key configured."}

    if _cache["payload"] and not refresh and time.time() - _cache["at"] < _TTL_SECONDS:
        return _cache["payload"]

    try:
        data = _fetch(base_url, api_key)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"supported": False, "detail": f"Provider did not report credits: {exc}"}

    usage = float(data.get("usage") or 0.0)
    limit = data.get("limit")            # null = no hard cap on this key
    remaining = data.get("limit_remaining")

    payload = {
        "supported": True,
        "label": data.get("label"),
        "usage": round(usage, 4),
        "limit": float(limit) if limit is not None else None,
        "remaining": float(remaining) if remaining is not None else None,
        # A key with a limit and nothing left cannot run paid models: they 403 with
        # "Key limit exceeded". Free models keep working.
        "exhausted": remaining is not None and float(remaining) <= 0,
        "freeTier": bool(data.get("is_free_tier")),
    }
    _cache.update(at=time.time(), payload=payload)
    return payload
