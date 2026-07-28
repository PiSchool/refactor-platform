#!/usr/bin/env python3
"""Launch an isolated fixture-backed API for browser tests."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = REPO_ROOT / "server"
# Port and state directory are overridable so a second, independent instance can
# be started while another is still running.
PORT = int(os.getenv("RP_E2E_PORT", "18100"))
STATE_ROOT = Path(os.getenv("RP_E2E_STATE_DIR", str(REPO_ROOT / ".e2e" / "backend")))


def main() -> None:
    shutil.rmtree(STATE_ROOT, ignore_errors=True)
    STATE_ROOT.mkdir(parents=True)
    os.environ["RP_DATA_DIR"] = str(STATE_ROOT)
    os.environ["RP_PLUGINS_DIR"] = str(SERVER_ROOT / "tests" / "fixtures" / "plugins")
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("OPENROUTER_API_KEY", None)
    sys.path.insert(0, str(SERVER_ROOT))

    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()