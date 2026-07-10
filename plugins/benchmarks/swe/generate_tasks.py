"""Generate tasks.yaml from the SWE-Refactor dataset.

Source of truth is the release's top-level `pure_refactoring_data.json`: 1099
rows covering all 18 projects, each carrying its own `compileCommand`,
`compileJDK`, `projectName` and `filePathAfter`. (The per-project
`data/<proj>/<proj>_pure_refactoring_data.json` files are a 703-row subset of
it — do not use them.)

One task per row. The before-state row is stashed in params.row (build_prompt
reads an allow-listed subset); the workspace is a git checkout at the
before-commit (commitId^) exported from the project's bare mirror.

Run: python generate_tasks.py <data_dir> [out.yaml]
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

# project name → git URL (must match data_bootstrap.REPO_URLS)
PROJECT_URL = {
    "checkstyle": "https://github.com/checkstyle/checkstyle.git",
    "commons-io": "https://github.com/apache/commons-io.git",
    "commons-lang": "https://github.com/apache/commons-lang.git",
    "gson": "https://github.com/google/gson.git",
    "guava": "https://github.com/google/guava.git",
    "hertzbeat": "https://github.com/apache/hertzbeat.git",
    "hibernate-orm": "https://github.com/hibernate/hibernate-orm.git",
    "hibernate-search": "https://github.com/hibernate/hibernate-search.git",
    "jadx": "https://github.com/skylot/jadx.git",
    "javaparser": "https://github.com/javaparser/javaparser.git",
    "junit4": "https://github.com/junit-team/junit4.git",
    "junit5": "https://github.com/junit-team/junit5.git",
    "mockito": "https://github.com/mockito/mockito.git",
    "pmd": "https://github.com/pmd/pmd.git",
    "shardingsphere-elasticjob": "https://github.com/apache/shardingsphere-elasticjob.git",
    "shenyu": "https://github.com/apache/shenyu.git",
    "shiro": "https://github.com/apache/shiro.git",
    "zxing": "https://github.com/zxing/zxing.git",
}

DATASET = "pure_refactoring_data.json"

# tasks.yaml stays lean: only what the platform needs to schedule and evaluate.
# The heavy per-row payload (whole-file source, signatures, diff locations) is
# looked up from the dataset by uniqueId at prompt/eval time — embedding it here
# produced a 35 MB manifest that every startup had to parse.


def _mirror(mirrors_root: Path, url: str) -> Path:
    return mirrors_root / f"{hashlib.sha1(url.encode()).hexdigest()}.git"


def _before_commit(mirror: Path, commit: str) -> str | None:
    if not mirror.exists():
        return None
    r = subprocess.run(["git", "-C", str(mirror), "rev-parse", f"{commit}^"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def repair_command(command: str) -> str:
    """Close an unterminated quote in the dataset's `compileCommand`.

    93 commons-io rows ship a truncated surefire exclusion list —
    `-Dtest='!FileUtilsDeleteDirectoryLinuxTestCase,!ObservableInputStreamTest`
    with no closing quote. Passed to a shell it dies with a syntax error, which
    the evaluator would otherwise record as the agent breaking the build.
    """
    if command.count("'") % 2:
        return command + "'"
    return command


def normalize_jdk(value: object) -> str:
    """Dataset uses both '1.8' and '8' style majors."""
    v = str(value or "17").strip()
    return v.split(".")[-1] if v.startswith("1.") else v


def _dataset_path(data_dir: Path) -> Path:
    direct = data_dir / DATASET
    if direct.is_file():
        return direct
    found = next((p for p in data_dir.rglob(DATASET) if "__MACOSX" not in str(p)), None)
    if found is None:
        raise FileNotFoundError(f"{DATASET} not found under {data_dir}")
    return found


def generate(data_dir: Path, out: Path, mirrors_root: Path | None = None) -> int:
    mirrors_root = mirrors_root or (data_dir / "mirrors")
    rows = json.loads(_dataset_path(data_dir).read_text(encoding="utf-8"))
    tasks = []
    for row in rows:
        uid, commit = row.get("uniqueId"), row.get("commitId")
        project = row.get("projectName")
        url = PROJECT_URL.get(project)
        if not (uid and commit and url):
            continue
        before = _before_commit(_mirror(mirrors_root, url), commit)
        rtype = row.get("type", "")
        tasks.append({
            "task_key": f"{project}/{uid}",
            "title": f"{project}: {rtype}",
            "language": "java",
            # `<sha>^` is a valid tree-ish; git archive resolves it from the mirror.
            "workspace": {"type": "git", "source": url, "ref": before or f"{commit}^"},
            "instructions": f"Perform a {rtype} refactoring as described.",
            "params": {
                "project": project,
                "refactoringType": rtype,
                "compileCommand": repair_command(row["compileCommand"]),
                "compileJDK": normalize_jdk(row.get("compileJDK")),
                "uniqueId": uid,
                "filePathBefore": row.get("filePathBefore", ""),
                "filePathAfter": row.get("filePathAfter", ""),
            },
        })
    out.write_text(yaml.safe_dump({"tasks": tasks}, sort_keys=False, allow_unicode=True),
                   encoding="utf-8")
    return len(tasks)


if __name__ == "__main__":
    d = Path(sys.argv[1])
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "tasks.yaml"
    n = generate(d, dest)
    print(f"wrote {n} tasks to {dest}")
