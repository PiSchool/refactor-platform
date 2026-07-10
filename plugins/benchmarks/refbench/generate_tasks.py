"""Generate tasks.yaml from a microsoft/RefactorBench clone.

One task per (repo, taskId, mode). Instructions are embedded inline so plugin
discovery needs no data present; the repositories + test files are fetched by
data_bootstrap at deploy time and referenced by relative path.

Run: python generate_tasks.py <clone_root> [out.yaml]
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

MODES = {"base": "base_mapping.py", "lazy": "lazy_mapping.py", "descriptive": "descriptive_mapping.py"}

# cwd inside the repo copy where a task's tests resolve imports (from the POC).
CWD_HINT = {
    "ansible_refactor": "lib", "celery_refactor": "celery", "django_refactor": "django",
    "fastapi_refactor": "fastapi", "flask_refactor": "src", "requests_refactor": "src",
    "salt_refactor": "salt", "scrapy_refactor": "scrapy", "tornado_refactor": "tornado",
}


def _load_mapping(path: Path) -> dict[str, str]:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod.file_mapping)


def _norm(rel: str) -> str:
    return rel.replace("../", "", 1).lstrip("/")


def generate(clone_root: Path, out: Path) -> int:
    tasks = []
    for mode, mapping_file in MODES.items():
        mapping = _load_mapping(clone_root / "scripts" / mapping_file)
        for test_rel_raw, task_rel_raw in mapping.items():
            test_rel = _norm(test_rel_raw)
            task_rel = _norm(task_rel_raw)
            parts = Path(test_rel).parts
            if len(parts) < 3 or parts[0] != "tests":
                continue
            repo = parts[1]
            task_id = Path(task_rel).name.replace("-task.txt", "")
            task_abs = clone_root / task_rel
            if not task_abs.is_file() or not (clone_root / test_rel).is_file():
                continue
            instructions = task_abs.read_text(encoding="utf-8").strip()
            tasks.append({
                "task_key": f"{repo}/{task_id}#{mode}",
                "title": f"{repo}: {task_id} ({mode})",
                "language": "python",
                "workspace": {"type": "snapshot", "source": f"repositories/{repo}"},
                "instructions": instructions,
                "params": {"mode": mode, "repo": repo, "test_file": test_rel,
                           "cwd_hint": CWD_HINT.get(repo, "")},
            })
    tasks.sort(key=lambda t: t["task_key"])
    out.write_text(yaml.safe_dump({"tasks": tasks}, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return len(tasks)


if __name__ == "__main__":
    root = Path(sys.argv[1])
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "tasks.yaml"
    n = generate(root, dest)
    print(f"wrote {n} tasks to {dest}")
