"""Benchmark data readiness. A benchmark ships a `data_bootstrap.py` with a
`bootstrap(data_dir)` function; the platform runs it once (background at
startup, or via CLI) and marks readiness with a `.ready` sentinel.
"""
from __future__ import annotations

import importlib.util
import threading
from pathlib import Path

from app.catalog.loader import LoadedBenchmark, Registry, discover


def data_state(loaded: LoadedBenchmark) -> str:
    if loaded.manifest.data is None:
        return "ready"  # no external data needed
    if (loaded.data_dir / ".ready").is_file():
        return "ready"
    if (loaded.data_dir / ".error").is_file():
        return "error"
    return "missing"


def _bootstrap_fn(loaded: LoadedBenchmark):
    assert loaded.manifest.data is not None
    path = loaded.plugin_dir / loaded.manifest.data.bootstrap
    spec = importlib.util.spec_from_file_location(f"rp_bootstrap_{loaded.manifest.key}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.bootstrap


def run_bootstrap(loaded: LoadedBenchmark) -> None:
    if loaded.manifest.data is None or data_state(loaded) == "ready":
        return
    loaded.data_dir.mkdir(parents=True, exist_ok=True)
    err = loaded.data_dir / ".error"
    err.unlink(missing_ok=True)
    try:
        _bootstrap_fn(loaded)(loaded.data_dir)
        (loaded.data_dir / ".ready").write_text("ok\n")
    except Exception as exc:
        err.write_text(f"{exc}\n")
        raise


def start_background_bootstrap(registry: Registry) -> None:
    pending = [b for b in registry.benchmarks.values() if data_state(b) != "ready" and b.manifest.data]
    for loaded in pending:
        threading.Thread(target=_safe_run, args=(loaded,), daemon=True).start()


def _safe_run(loaded: LoadedBenchmark) -> None:
    try:
        run_bootstrap(loaded)
    except Exception:
        pass  # error sentinel already written; surfaced via catalog data_state


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
