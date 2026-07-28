"""A language server offered to the S1+LSP setup for one language.

`ensure()` reports whether the server can run here; a setup that needs it is
refused with the reason rather than starting without it. `server_config()`
returns what the agent's CLI needs in order to talk to it.

Imports only from `app.catalog.sdk`.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app.catalog.sdk import LSPPlugin

BINARY = "pylsp"


class Plugin(LSPPlugin):
    def ensure(self) -> tuple[bool, str]:
        path = shutil.which(BINARY)
        if path:
            return True, path
        return False, f"{BINARY} is not on PATH; install it with: pip install python-lsp-server"

    def server_config(self, workspace: Path) -> dict:
        return {
            "command": BINARY,
            "args": [],
            "rootPath": str(workspace),
            "languages": ["python"],
        }
