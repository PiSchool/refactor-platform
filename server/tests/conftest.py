from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER_DIR))


@pytest.fixture()
def tmp_env(tmp_path, monkeypatch):
    """Isolated data dir + fresh engine per test."""
    from app import config
    from app.db import engine as db_engine

    monkeypatch.setenv("RP_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config.get_settings.cache_clear()
    db_engine.reset_for_tests()
    yield tmp_path
    config.get_settings.cache_clear()
    db_engine.reset_for_tests()
