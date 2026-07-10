from __future__ import annotations

import io
import json
from contextlib import contextmanager


def _fake_urlopen(payload):
    @contextmanager
    def _open(req, timeout=0):
        yield io.BytesIO(json.dumps(payload).encode())

    def urlopen(req, timeout=0):
        return _open(req, timeout)

    return urlopen


def test_catalog_offers_only_models_that_can_drive_an_agent(monkeypatch):
    """A music model (text+audio out, no tool calling) must never reach the wizard."""
    from app.api import models as mod

    payload = {"data": [
        {"id": "google/lyria-3-clip-preview", "pricing": {"prompt": "0", "completion": "0"},
         "architecture": {"output_modalities": ["text", "audio"]}, "supported_parameters": ["max_tokens"]},
        {"id": "anthropic/claude-sonnet-4.5", "pricing": {"prompt": "0.000003", "completion": "0.000015"},
         "architecture": {"output_modalities": ["text"]}, "supported_parameters": ["tools", "max_tokens"]},
        {"id": "some/embedding", "pricing": {"prompt": "0", "completion": "0"},
         "architecture": {"output_modalities": ["embedding"]}, "supported_parameters": ["tools"]},
    ]}
    monkeypatch.setattr(mod.urllib.request, "urlopen", _fake_urlopen(payload))
    assert [m["id"] for m in mod._fetch("https://x/api/v1", "k")] == ["anthropic/claude-sonnet-4.5"]


def test_catalog_keeps_everything_when_the_provider_declares_no_capabilities(monkeypatch):
    """Plain OpenAI-compatible endpoints publish no supported_parameters at all."""
    from app.api import models as mod

    payload = {"data": [{"id": "local/llama", "pricing": {"prompt": "0", "completion": "0"}}]}
    monkeypatch.setattr(mod.urllib.request, "urlopen", _fake_urlopen(payload))
    assert [m["id"] for m in mod._fetch("https://x/api/v1", "k")] == ["local/llama"]
