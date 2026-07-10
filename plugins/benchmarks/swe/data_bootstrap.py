"""Fetch SWE-Refactor data ahead of runs.

Downloads the Zenodo release (per-project task JSONs + RefactoringMiner) into
the plugin data dir, and creates full bare mirrors of the Java project repos so
each task's before-commit is available offline. No network at task time.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ZENODO_URL = "https://zenodo.org/records/17655592/files/SWE-Refactor.zip?download=1"

REPO_URLS = [
    "https://github.com/checkstyle/checkstyle.git",
    "https://github.com/apache/commons-io.git",
    "https://github.com/apache/commons-lang.git",
    "https://github.com/google/gson.git",
    "https://github.com/google/guava.git",
    "https://github.com/apache/hertzbeat.git",
    "https://github.com/hibernate/hibernate-orm.git",
    "https://github.com/hibernate/hibernate-search.git",
    "https://github.com/skylot/jadx.git",
    "https://github.com/javaparser/javaparser.git",
    "https://github.com/junit-team/junit4.git",
    "https://github.com/junit-team/junit5.git",
    "https://github.com/mockito/mockito.git",
    "https://github.com/pmd/pmd.git",
    "https://github.com/apache/shardingsphere-elasticjob.git",
    "https://github.com/apache/shenyu.git",
    "https://github.com/apache/shiro.git",
    "https://github.com/zxing/zxing.git",
]


def mirror_dir(mirrors_root: Path, url: str) -> Path:
    return mirrors_root / f"{hashlib.sha1(url.encode()).hexdigest()}.git"


def _valid_zip(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as z:
            return z.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def _download(url: str, dest: Path, attempts: int = 5) -> None:
    """Fetch to dest, verifying the full Content-Length. urlretrieve silently
    keeps truncated bodies when Zenodo drops a large connection; verify + retry.
    """
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                expected = int(r.headers.get("Content-Length") or 0)
                with open(dest, "wb") as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
            if expected and dest.stat().st_size != expected:
                raise OSError(f"short read: {dest.stat().st_size}/{expected}")
            return
        except (OSError, urllib.error.URLError) as exc:
            if attempt == attempts:
                raise
            print(f"  download retry {attempt}/{attempts} ({exc})", file=sys.stderr)


def bootstrap(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    if not (data_dir / "data").is_dir() or not (data_dir / "tools").is_dir():
        zpath = data_dir / "SWE-Refactor.zip"
        if not zpath.is_file() or not _valid_zip(zpath):
            _download(ZENODO_URL, zpath)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(data_dir)
        _flatten(data_dir)
        rm = next(data_dir.rglob("RefactoringMiner"), None)
        if rm is not None and rm.is_file():
            rm.chmod(0o755)

    mirrors_root = _shared_mirrors_root()
    mirrors_root.mkdir(parents=True, exist_ok=True)
    for url in REPO_URLS:
        dest = mirror_dir(mirrors_root, url)
        if not dest.exists():
            subprocess.run(["git", "clone", "--mirror", url, str(dest)], check=False)


def _shared_mirrors_root() -> Path:
    import os
    return Path(os.getenv("RP_DATA_DIR", str(Path.home() / "refactor-platform" / "data"))) / "mirrors"


def _flatten(data_dir: Path) -> None:
    """Normalize the extracted release to `<data_dir>/data/…`.

    The real Zenodo zip nests the usable dataset at `code/data/` (per-project
    `*_pure_refactoring_data.json` + `tools/RefactoringMiner-…`). Lift that to
    `<data_dir>/data`. Fall back to the single-`SWE-Refactor/`-dir layout.
    """
    src = data_dir / "code" / "data"
    if src.is_dir():
        dest = data_dir / "data"
        if dest.exists():
            shutil.rmtree(dest)
        src.rename(dest)
        return
    inner = data_dir / "SWE-Refactor"
    if inner.is_dir():
        for item in inner.iterdir():
            item.rename(data_dir / item.name)


if __name__ == "__main__":
    bootstrap(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data")
