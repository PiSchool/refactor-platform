"""Fetch RefactorBench data into the plugin data dir (once, ahead of runs).

Clones microsoft/RefactorBench and keeps repositories/, tests/, scripts/,
problems/. Regenerates tasks.yaml if absent. No network at task time.
"""
from __future__ import annotations

import importlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_URL = "https://github.com/microsoft/RefactorBench.git"
KEEP = ("repositories", "tests", "scripts", "problems")


def _sibling(name: str):
    """Import a module from this plugin's directory, private to this plugin.

    Loaded by the platform this is a relative import. Run directly it is loaded
    by path. Neither becomes a bare global name that a second benchmark shipping
    the same file name would then receive instead of its own.
    """
    if __package__:
        return importlib.import_module(f".{name}", __package__)
    source = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"{Path(__file__).parent.name}_{name}", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        _sibling("generate_tasks").generate(data_dir, tasks_yaml)


if __name__ == "__main__":
    bootstrap(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data")
