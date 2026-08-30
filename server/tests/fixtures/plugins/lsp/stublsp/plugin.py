from __future__ import annotations

import sys
from pathlib import Path

from app.catalog.sdk import LSPPlugin


class Plugin(LSPPlugin):
    language = "python"

    def ensure(self) -> tuple[bool, str]:
        return True, sys.executable

    def server_config(self, workspace: Path) -> dict:
        server = Path(__file__).with_name("server.py")
        return {
            "command": sys.executable,
            "args": [str(server)],
            "fileExtensions": {".py": "python"},
        }
