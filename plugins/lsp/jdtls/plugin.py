from __future__ import annotations

import os
import shutil
from pathlib import Path

from app.catalog.sdk import LSPPlugin


class Plugin(LSPPlugin):
    language = "java"

    def ensure(self) -> tuple[bool, str]:
        exe = shutil.which("jdtls")
        if not exe:
            return False, "jdtls not on PATH"
        java_home = os.getenv("JDK_21_HOME", "").strip()
        java = Path(java_home) / "bin" / "java" if java_home else None
        if java is not None and (not java.is_file() or not os.access(java, os.X_OK)):
            return False, f"JDK_21_HOME has no Java executable: {java_home}"
        return True, exe

    def server_config(self, workspace: Path) -> dict:
        exe = shutil.which("jdtls") or "jdtls"
        java_home = os.getenv("JDK_21_HOME", "").strip()
        if java_home:
            env = shutil.which("env") or "/usr/bin/env"
            path = os.pathsep.join((str(Path(java_home) / "bin"), os.getenv("PATH", "")))
            return {
                "command": env,
                "args": [f"JAVA_HOME={java_home}", f"PATH={path}", exe],
                "fileExtensions": {".java": "java"},
            }
        return {"command": exe, "args": [], "fileExtensions": {".java": "java"}}
