from __future__ import annotations

import shutil
from pathlib import Path

from app.catalog.sdk import LSPPlugin


class Plugin(LSPPlugin):
    language = "python"

    def ensure(self) -> tuple[bool, str]:
        exe = shutil.which("pylsp")
        return (bool(exe), exe or "pylsp not on PATH")

    def server_config(self, workspace: Path) -> dict:
        return {"command": "pylsp", "args": [], "fileExtensions": {".py": "python"}}
