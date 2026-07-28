"""An adapter whose CLI is not installed must be refused, not launched.

Before this, selecting an agent whose binary was absent produced a task that
died inside the PTY with a shell error, attributed to the agent.
"""
from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from tests.helpers import FIXTURES

PLUGINS = Path(__file__).resolve().parents[2] / "plugins"


def _loaded(binary: str, install: str = ""):
    from app.catalog.loader import LoadedAgent
    from app.catalog.manifest import AgentManifest
    from app.catalog.sdk import AgentPlugin, CommandSpec

    class _Adapter(AgentPlugin):
        def prepare(self, session):
            return None

        def command(self, session):
            return CommandSpec(argv=["true"], env={}, cwd=session.workspace)

        def events_path(self, session):
            return None

        def parse_session(self, events_path, terminal_log_path):
            raise NotImplementedError

    manifest = AgentManifest(type="agent", key="k", name="k", binary=binary, install=install)
    return LoadedAgent(manifest=manifest, plugin_dir=Path("."), impl=_Adapter())


def test_agent_without_declared_binary_is_always_available():
    assert _loaded("").available is True
    assert _loaded("").binary_path is None
    assert _loaded("").unavailable_reason() == ""


def test_declared_binary_is_resolved_on_path():
    loaded = _loaded("sh")
    assert loaded.available is True
    assert loaded.binary_path and loaded.binary_path.endswith("sh")


def test_missing_binary_reports_the_install_command():
    loaded = _loaded("definitely-not-installed-cli", "npm install -g example")
    assert loaded.available is False
    reason = loaded.unavailable_reason()
    assert "definitely-not-installed-cli" in reason
    assert "npm install -g example" in reason


def test_shipped_adapters_declare_their_cli():
    from app.catalog.loader import discover

    registry = discover(PLUGINS)
    assert registry.errors == []
    binaries = {key: loaded.manifest.binary for key, loaded in registry.agents.items()}
    assert binaries["copilot"] == "copilot"
    assert binaries["codex"] == "codex"
    assert binaries["aider"] == "aider"
    for key, loaded in registry.agents.items():
        assert loaded.manifest.install, f"{key} must tell the operator how to install its CLI"


def test_shipped_adapter_capabilities_are_declared_not_assumed():
    from app.catalog.loader import discover

    registry = discover(PLUGINS)
    # aider edits through the model's reply: no MCP client, so no S2 setups.
    assert registry.agents["aider"].impl.capabilities["retrieval"] is False
    assert registry.agents["aider"].impl.capabilities["lsp"] is False
    # codex calls MCP servers and shells out, but has no sub-agent mode.
    assert registry.agents["codex"].impl.capabilities["retrieval"] is True
    assert registry.agents["codex"].impl.capabilities["subagents"] is False


@pytest.fixture()
async def client(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    from app import config

    config.get_settings.cache_clear()
    from app.main import app

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.mark.asyncio
async def test_catalog_publishes_availability(client):
    catalog = (await client.get("/api/catalog")).json()
    agent = next(a for a in catalog["agents"] if a["key"] == "stub")
    assert agent["available"] is True
    assert "binary" in agent and "install" in agent


@pytest.mark.asyncio
async def test_no_agent_advertises_a_model_allow_list(client):
    """A run reaches one provider, and any model id that provider serves is
    valid for any agent, so the model is the deployment's choice. Neither the
    manifest schema nor the catalogue offers a per-agent list to filter by."""
    from app.catalog.manifest import AgentManifest

    assert "models" not in AgentManifest.model_fields
    catalog = (await client.get("/api/catalog")).json()
    assert catalog["agents"]
    assert all("models" not in agent for agent in catalog["agents"])


@pytest.mark.asyncio
async def test_run_creation_refuses_an_uninstalled_cli(client, monkeypatch):
    catalog = (await client.get("/api/catalog")).json()
    bench = next(b for b in catalog["benchmarks"] if b["key"] == "fixturebench")
    agent = next(a for a in catalog["agents"] if a["key"] == "stub")

    from app.main import app

    loaded = app.state.registry.agents["stub"]
    monkeypatch.setattr(type(loaded.manifest), "model_config",
                        {**type(loaded.manifest).model_config, "frozen": False}, raising=False)
    loaded.manifest.binary = "definitely-not-installed-cli"
    loaded.manifest.install = "pip install example"
    try:
        body = {"benchmarkId": bench["id"], "setupId": "s1", "agentToolId": agent["id"],
                "model": "stub-model", "taskKeys": ["fixture-0001"], "taskTimeoutSeconds": 30}
        response = await client.post("/api/runs", json=body)
        assert response.status_code == 422
        assert "definitely-not-installed-cli" in response.json()["detail"]
        assert "pip install example" in response.json()["detail"]

        catalog = (await client.get("/api/catalog")).json()
        assert next(a for a in catalog["agents"] if a["key"] == "stub")["available"] is False
    finally:
        loaded.manifest.binary = ""
        loaded.manifest.install = ""
