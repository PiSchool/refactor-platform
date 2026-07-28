"""A redeploy has to be verifiable.

A rebuilt container looks exactly like the one it replaced, so an operator who
ran `docker compose up -d --build` had no way to tell whether the image carried
their changes. These tests hold the identity contract: the fingerprint follows
the source that decides behaviour, ignores what only ships alongside it, and is
the same value whether the code runs from an image or from a checkout.
"""
from __future__ import annotations

import httpx
import pytest

from app import build_info
from tests.helpers import FIXTURES


def _tree(root, *, server: str = "print('a')\n", plugin: str = "key: a\n", config: str = "a: 1\n"):
    """A checkout-shaped tree: server/app, plugins, config.yaml."""
    (root / "server" / "app").mkdir(parents=True)
    (root / "server" / "app" / "main.py").write_text(server)
    (root / "plugins" / "agents" / "demo").mkdir(parents=True)
    (root / "plugins" / "agents" / "demo" / "plugin.yaml").write_text(plugin)
    (root / "config.yaml").write_text(config)
    return root


def test_fingerprint_follows_source_and_ignores_what_only_ships_alongside_it(tmp_path):
    root = _tree(tmp_path / "repo")
    original = build_info.tree_fingerprint(root)
    assert len(original) == 12

    # benchmark data is bootstrapped into a volume after the build, caches and
    # plugin tests do not change what a run does: none of them may move the value
    data = root / "plugins" / "benchmarks" / "swe" / "data"
    data.mkdir(parents=True)
    (data / "tasks.json").write_text("[]")
    (root / "plugins" / "benchmarks" / "swe" / ".ready").write_text("")
    (root / "plugins" / "agents" / "demo" / "tests").mkdir()
    (root / "plugins" / "agents" / "demo" / "tests" / "test_demo.py").write_text("assert True\n")
    cache = root / "server" / "app" / "__pycache__"
    cache.mkdir()
    (cache / "main.cpython-312.pyc").write_bytes(b"\x00")
    assert build_info.tree_fingerprint(root) == original

    (root / "server" / "app" / "main.py").write_text("print('b')\n")
    assert build_info.tree_fingerprint(root) != original


@pytest.mark.parametrize("changed", ["plugin", "config"])
def test_a_plugin_or_configuration_change_is_a_different_deployment(tmp_path, changed):
    root = _tree(tmp_path / "repo")
    before = build_info.tree_fingerprint(root)
    if changed == "plugin":
        (root / "plugins" / "agents" / "demo" / "plugin.yaml").write_text("key: b\n")
    else:
        (root / "config.yaml").write_text("a: 2\n")
    assert build_info.tree_fingerprint(root) != before


def test_the_same_code_reports_the_same_identity_from_an_image_and_a_checkout(tmp_path):
    """The comparison is only useful if both layouts agree.

    The image keeps the server package at /app/server/app and config.yaml next to
    it; a checkout keeps config.yaml at the repository root. Identical content
    has to fingerprint identically regardless.
    """
    checkout = _tree(tmp_path / "repo")
    image = tmp_path / "image"
    (image / "server" / "app").mkdir(parents=True)
    (image / "server" / "app" / "main.py").write_text("print('a')\n")
    (image / "plugins" / "agents" / "demo").mkdir(parents=True)
    (image / "plugins" / "agents" / "demo" / "plugin.yaml").write_text("key: a\n")
    (image / "server" / "config.yaml").write_text("a: 1\n")

    assert build_info.fingerprint(
        server_package=image / "server" / "app",
        plugins_dir=image / "plugins",
        config=image / "server" / "config.yaml",
    ) == build_info.tree_fingerprint(checkout)


def test_an_unstamped_build_reports_no_revision_rather_than_inventing_one(monkeypatch, tmp_path):
    monkeypatch.delenv("RP_BUILD_REV", raising=False)
    monkeypatch.delenv("RP_BUILD_TIME", raising=False)
    monkeypatch.setenv("RP_BUILD_STAMP", str(tmp_path / "absent"))
    assert build_info.stamp() == {"revision": "", "builtAt": ""}

    stamp = tmp_path / "build-stamp"
    stamp.write_text("revision=abc1234\nbuiltAt=2026-07-26T18:00:00Z\n")
    monkeypatch.setenv("RP_BUILD_STAMP", str(stamp))
    assert build_info.stamp() == {"revision": "abc1234", "builtAt": "2026-07-26T18:00:00Z"}

    # a deployment that runs the code outside an image build can still declare it
    monkeypatch.setenv("RP_BUILD_REV", "local")
    assert build_info.stamp()["revision"] == "local"


@pytest.fixture()
async def client(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    from app import config
    config.get_settings.cache_clear()
    build_info.running_fingerprint.cache_clear()
    from app.main import app
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.mark.asyncio
async def test_health_and_services_say_what_this_deployment_was_built_from(client):
    health = (await client.get("/api/health")).json()
    assert len(health["build"]["fingerprint"]) == 12
    assert set(health["build"]) == {"fingerprint", "revision", "builtAt"}

    groups = {g["key"]: g for g in (await client.get("/api/system")).json()["groups"]}
    rows = {r["name"]: r for r in groups["deployment"]["rows"]}
    assert rows["Backend"]["value"] == health["build"]["fingerprint"]
    assert "fingerprint" in rows["Backend"]["detail"]
    # unstamped here, so no revision is claimed
    assert "Revision" not in rows
