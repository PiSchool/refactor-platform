from __future__ import annotations

import shutil
from pathlib import Path

from app.catalog.sdk import LSPPlugin


class Plugin(LSPPlugin):
    language = "java"

    def ensure(self) -> tuple[bool, str]:
        exe = shutil.which("jdtls")
        return (bool(exe), exe or "jdtls not on PATH")

    def server_config(self, workspace: Path) -> dict:
        return {"command": "jdtls", "args": [], "fileExtensions": {".java": "java"}}
