from __future__ import annotations

import io
import json
from contextlib import contextmanager


def _fake_urlopen(payload):
    @contextmanager
    def _open(req, timeout=0):
        yield io.BytesIO(json.dumps(payload).encode())

    return lambda req, timeout=0: _open(req, timeout)


def _reset(mod):
    mod._cache.update(at=0.0, payload=None)


def test_exhausted_key_is_reported_as_exhausted(monkeypatch, tmp_env):
    """$600/$600 with 0 remaining: paid models 403, and the UI must say so."""
    from app.api import credits as mod

    _reset(mod)
    monkeypatch.setattr(mod, "get_settings", lambda: type("S", (), {
        "provider_base_url": lambda self=None: "https://openrouter.ai/api/v1",
        "provider_api_key": lambda self=None: "sk-or-v1-x"})())
    monkeypatch.setattr(mod.urllib.request, "urlopen",
                        _fake_urlopen({"data": {"usage": 600.057, "limit": 600, "limit_remaining": 0}}))

    c = mod.credits(refresh=True)
    assert c["supported"] and c["exhausted"] is True
    assert c["usage"] == 600.057 and c["limit"] == 600.0 and c["remaining"] == 0.0


def test_key_with_no_cap_is_not_exhausted(monkeypatch, tmp_env):
    from app.api import credits as mod

    _reset(mod)
    monkeypatch.setattr(mod, "get_settings", lambda: type("S", (), {
        "provider_base_url": lambda self=None: "https://openrouter.ai/api/v1",
        "provider_api_key": lambda self=None: "sk-or-v1-x"})())
    monkeypatch.setattr(mod.urllib.request, "urlopen",
                        _fake_urlopen({"data": {"usage": 0, "limit": None, "limit_remaining": None}}))

    c = mod.credits(refresh=True)
    assert c["exhausted"] is False and c["limit"] is None and c["remaining"] is None


def test_provider_without_credit_endpoint_says_unknown(monkeypatch, tmp_env):
    """A plain OpenAI-compatible endpoint 404s; never invent a balance."""
    from app.api import credits as mod

    _reset(mod)
    monkeypatch.setattr(mod, "get_settings", lambda: type("S", (), {
        "provider_base_url": lambda self=None: "https://example/v1",
        "provider_api_key": lambda self=None: "k"})())

    def boom(req, timeout=0):
        raise OSError("404")

    monkeypatch.setattr(mod.urllib.request, "urlopen", boom)
    c = mod.credits(refresh=True)
    assert c["supported"] is False and "did not report" in c["detail"]
