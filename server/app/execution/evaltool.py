"""S1-eval in-session self-check. Writes an eval.sh into the workspace that
runs the benchmark's verify pipeline in advisory (leak-safe) mode, capped.
"""
from __future__ import annotations

import fcntl
import json
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT = """#!/usr/bin/env bash
exec {python} -m app.evaluation.check --run-task {run_task_id} --max-attempts {max_attempts}
"""


def install(run_task_id: str, workspace: Path, max_attempts: int) -> Path:
    script = workspace / "eval.sh"
    script.write_text(_SCRIPT.format(
        max_attempts=max(1, max_attempts), python=shlex.quote(sys.executable),
        run_task_id=shlex.quote(run_task_id)), encoding="utf-8")
    script.chmod(0o755)
    return script


def checks_dir(task_artifacts: Path) -> Path:
    return task_artifacts / "eval" / "self-checks"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _write_text(path: Path, value: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(value, encoding="utf-8")
    tmp.replace(path)


def reserve_attempt(task_artifacts: Path, max_attempts: int) -> tuple[int, Path] | None:
    root = checks_dir(task_artifacts)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".attempts.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        count_path = root / ".attempts.count"
        try:
            completed = int(count_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            completed = 0
        existing = []
        for path in root.glob("attempt-*"):
            try:
                existing.append(int(path.name.removeprefix("attempt-")))
            except ValueError:
                continue
        completed = max([completed, *existing])
        if completed >= max(1, max_attempts):
            _write_json(root / "limit-reached.json", {
                "schemaVersion": 1,
                "status": "attempt_limit",
                "maxAttempts": max(1, max_attempts),
                "observedAt": datetime.now(timezone.utc).isoformat(),
            })
            return None
        attempt = completed + 1
        attempt_dir = root / f"attempt-{attempt:04d}"
        attempt_dir.mkdir(parents=True, exist_ok=False)
        _write_text(count_path, f"{attempt}\n")
        _write_json(attempt_dir / "result.json", {
            "schemaVersion": 1,
            "attempt": attempt,
            "status": "running",
            "startedAt": datetime.now(timezone.utc).isoformat(),
        })
        return attempt, attempt_dir


def write_attempt(attempt_dir: Path, payload: dict) -> None:
    _write_json(attempt_dir / "result.json", payload)


def attempt_results(task_artifacts: Path) -> list[dict]:
    rows: list[dict] = []
    for result in checks_dir(task_artifacts).glob("attempt-*/result.json"):
        try:
            row = json.loads(result.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if row.get("status") in {"passed", "failed", "error"}:
            rows.append(row)
    return sorted(rows, key=lambda row: int(row.get("attempt", 0)))


def completed_attempts(task_artifacts: Path) -> int:
    return len(attempt_results(task_artifacts))
