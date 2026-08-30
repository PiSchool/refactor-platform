"""Benchmark data readiness. A benchmark ships a `data_bootstrap.py` with a
`bootstrap(data_dir)` function; the platform runs it once (background at
startup, or via CLI) and marks readiness with a `.ready` sentinel.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from app.catalog.loader import LoadedBenchmark, Registry, discover, import_plugin_module


logger = logging.getLogger(__name__)
_active_guard = threading.Lock()
_active: set[Path] = set()


def _job_key(loaded: LoadedBenchmark) -> Path:
    return loaded.data_dir.resolve()


def _is_active(loaded: LoadedBenchmark) -> bool:
    with _active_guard:
        return _job_key(loaded) in _active


def _expected_revision(loaded: LoadedBenchmark) -> str:
    data = loaded.manifest.data
    return getattr(data, "revision", "ok") if data is not None else "ok"


def _marker_ready(loaded: LoadedBenchmark) -> bool:
    marker = loaded.data_dir / ".ready"
    if not marker.is_file():
        return False
    try:
        return marker.read_text(encoding="utf-8").strip() == _expected_revision(loaded)
    except OSError:
        return False


def data_state(loaded: LoadedBenchmark) -> str:
    if loaded.manifest.data is None:
        return "ready"  # no external data needed
    if _marker_ready(loaded):
        return "ready"
    if _is_active(loaded):
        return "provisioning"
    if (loaded.data_dir / ".error").is_file():
        return "error"
    return "missing"


def bootstrap_error(loaded: LoadedBenchmark) -> str:
    error_path = loaded.data_dir / ".error"
    if not error_path.is_file():
        return ""
    try:
        return error_path.read_text(encoding="utf-8").strip()[:2000]
    except OSError:
        return "Benchmark provisioning failed; the error marker could not be read."


def _bootstrap_fn(loaded: LoadedBenchmark):
    """The benchmark's `bootstrap(data_dir)`, imported like any plugin module.

    Two benchmarks may ship a helper of the same name, and provisioning runs in
    a thread per benchmark, so this goes through the loader's isolation rather
    than importing the file into the process's own module namespace.
    """
    assert loaded.manifest.data is not None
    stem = Path(loaded.manifest.data.bootstrap).stem
    return import_plugin_module(loaded.plugin_dir, stem).bootstrap


def _claim(loaded: LoadedBenchmark) -> bool:
    if loaded.manifest.data is None or _marker_ready(loaded):
        return False
    key = _job_key(loaded)
    with _active_guard:
        if key in _active:
            return False
        _active.add(key)
    return True


def _release(loaded: LoadedBenchmark) -> None:
    with _active_guard:
        _active.discard(_job_key(loaded))


def _write_marker(path: Path, text: str) -> None:
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _publish_state(loaded: LoadedBenchmark) -> None:
    """Notify the dashboard without making it poll the complete settings API."""
    from app.realtime.hub import hub

    hub.publish_threadsafe(
        f"benchmark:{loaded.manifest.key}",
        "status",
        {
            "key": loaded.manifest.key,
            "dataState": data_state(loaded),
            "dataError": bootstrap_error(loaded),
        },
    )


def _run_claimed(loaded: LoadedBenchmark) -> None:
    loaded.data_dir.mkdir(parents=True, exist_ok=True)
    err = loaded.data_dir / ".error"
    err.unlink(missing_ok=True)
    (loaded.data_dir / ".ready").unlink(missing_ok=True)
    logger.info("Provisioning benchmark data: %s", loaded.manifest.key)
    try:
        _bootstrap_fn(loaded)(loaded.data_dir)
        _write_marker(loaded.data_dir / ".ready", f"{_expected_revision(loaded)}\n")
        logger.info("Benchmark data ready: %s", loaded.manifest.key)
    except Exception as exc:
        _write_marker(err, f"{exc}\n")
        logger.exception("Benchmark data provisioning failed: %s", loaded.manifest.key)
        raise
    finally:
        _release(loaded)
        _publish_state(loaded)


def run_bootstrap(loaded: LoadedBenchmark) -> bool:
    """Provision synchronously if no job already owns this benchmark.

    The boolean reports whether this caller acquired and ran the job. Duplicate
    startup, API, or CLI requests never execute a second writer.
    """
    if not _claim(loaded):
        return False
    _run_claimed(loaded)
    return True


def start_background_bootstrap(registry: Registry) -> None:
    for loaded in registry.benchmarks.values():
        start_background_bootstrap_one(loaded)


def start_background_bootstrap_one(loaded: LoadedBenchmark) -> bool:
    """Start at most one daemon job for a benchmark and return whether it began."""
    if not _claim(loaded):
        return False
    threading.Thread(
        target=_safe_run_claimed,
        args=(loaded,),
        daemon=True,
        name=f"bootstrap-{loaded.manifest.key}",
    ).start()
    return True


def _safe_run_claimed(loaded: LoadedBenchmark) -> None:
    try:
        _run_claimed(loaded)
    except Exception:
        pass  # logged and persisted by _run_claimed; surfaced through the API


def main(argv: list[str] | None = None) -> int:
    import sys

    from app.config import get_settings

    argv = argv if argv is not None else sys.argv[1:]
    registry = discover(get_settings().plugins_dir)
    keys = argv or list(registry.benchmarks)
    for key in keys:
        loaded = registry.benchmarks.get(key)
        if not loaded:
            print(f"unknown benchmark: {key}")
            continue
        print(f"bootstrapping {key} …")
        run_bootstrap(loaded)
        print(f"  {key}: {data_state(loaded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
