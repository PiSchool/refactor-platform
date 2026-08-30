from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SERVER_DIR))
sys.path.insert(0, str(TESTS_DIR))

# Retrieval is mandatory and its embeddings come from the model server, which a
# test run does not have. The tests therefore embed through the product's own
# `RETRIEVAL_EMBEDDER` hook, deterministically; see tests/fixtures/embedder.py.
# PYTHONPATH carries it into the MCP server the agent CLI starts as a subprocess.
os.environ.setdefault("RETRIEVAL_EMBEDDER", "fixtures.embedder:build")
os.environ["PYTHONPATH"] = os.pathsep.join(
    part for part in (str(TESTS_DIR), os.environ.get("PYTHONPATH", "")) if part
)


@pytest.fixture()
async def tmp_env(tmp_path, monkeypatch):
    """Isolated data dir + fresh engine per test."""
    from app import config
    from app.db import engine as db_engine

    await db_engine.dispose()
    monkeypatch.setenv("RP_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config.get_settings.cache_clear()
    yield tmp_path
    await db_engine.dispose()
    config.get_settings.cache_clear()
