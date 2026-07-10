"""Fetch RefactorBench data into the plugin data dir (once, ahead of runs).

Clones microsoft/RefactorBench and keeps repositories/, tests/, scripts/,
problems/. Regenerates tasks.yaml if absent. No network at task time.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_URL = "https://github.com/microsoft/RefactorBench.git"
KEEP = ("repositories", "tests", "scripts", "problems")


def bootstrap(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    if all((data_dir / d).is_dir() for d in KEEP):
        return
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "RefactorBench"
        subprocess.run(["git", "clone", "--depth=1", REPO_URL, str(clone)], check=True)
        for d in KEEP:
            src = clone / d
            if src.is_dir():
                shutil.copytree(src, data_dir / d, dirs_exist_ok=True)
    # (re)generate tasks.yaml next to the plugin if missing
    tasks_yaml = Path(__file__).parent / "tasks.yaml"
    if not tasks_yaml.is_file():
        sys.path.insert(0, str(Path(__file__).parent))
        import generate_tasks
        generate_tasks.generate(data_dir, tasks_yaml)


if __name__ == "__main__":
    bootstrap(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data")
