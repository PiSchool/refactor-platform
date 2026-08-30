"""Fetch SWE-Refactor data ahead of runs.

Downloads the Zenodo release (per-project task JSONs + RefactoringMiner) into
the plugin data dir, and creates full bare mirrors of the Java project repos so
each task's before-commit is available offline. No network at task time.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

import yaml

ZENODO_URL = "https://zenodo.org/records/17655592/files/SWE-Refactor.zip?download=1"
DATASET = "pure_refactoring_data.json"
MINER = Path("data/tools/RefactoringMiner-3.0.10/bin/RefactoringMiner")
TASKS_FILE = Path(__file__).with_name("tasks.yaml")

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
    """Fetch and validate a complete ZIP before atomically replacing ``dest``.

    Zenodo can drop a large transfer early. Writing into the final archive also
    allowed a concurrent bootstrap reader to open a half-written ZIP, so each
    attempt now uses a same-filesystem temporary file and only publishes it
    after both Content-Length and CRC validation pass.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, attempts + 1):
        fd, name = tempfile.mkstemp(prefix=f".{dest.name}.", suffix=".part", dir=dest.parent)
        os.close(fd)
        temporary = Path(name)
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                expected = int(r.headers.get("Content-Length") or 0)
                with temporary.open("wb") as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
            if expected and temporary.stat().st_size != expected:
                raise OSError(f"short read: {temporary.stat().st_size}/{expected}")
            if not _valid_zip(temporary):
                raise OSError("downloaded archive failed ZIP integrity validation")
            temporary.replace(dest)
            return
        except (OSError, urllib.error.URLError, ValueError) as exc:
            if attempt == attempts:
                raise
            print(f"  download retry {attempt}/{attempts} ({exc})", file=sys.stderr)
        finally:
            temporary.unlink(missing_ok=True)


def bootstrap(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    if not _data_complete(data_dir):
        zpath = data_dir / "SWE-Refactor.zip"
        if not zpath.is_file() or not _valid_zip(zpath):
            print("Downloading SWE-Refactor release from Zenodo …", flush=True)
            _download(ZENODO_URL, zpath)
        _install_archive(zpath, data_dir)
    if not _data_complete(data_dir):
        raise RuntimeError(
            f"SWE-Refactor archive did not provide {DATASET} and {MINER.as_posix()}"
        )
    (data_dir / MINER).chmod(0o755)

    mirrors_root = _shared_mirrors_root()
    mirrors_root.mkdir(parents=True, exist_ok=True)
    revisions_by_repo = _task_revisions()
    for index, url in enumerate(REPO_URLS, start=1):
        print(f"Provisioning SWE repository mirror {index}/{len(REPO_URLS)}: {url}", flush=True)
        mirror = _ensure_mirror(mirrors_root, url)
        _ensure_task_revisions(mirror, revisions_by_repo.get(url, set()))


def _data_complete(data_dir: Path) -> bool:
    return (data_dir / DATASET).is_file() and (data_dir / MINER).is_file()


def _valid_mirror(path: Path) -> bool:
    if not path.is_dir():
        return False
    probe = subprocess.run(
        ["git", "--git-dir", str(path), "rev-parse", "--is-bare-repository"],
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0 and probe.stdout.strip() == "true"


def _ensure_mirror(mirrors_root: Path, url: str) -> Path:
    dest = mirror_dir(mirrors_root, url)
    if _valid_mirror(dest):
        return dest
    if dest.exists():
        shutil.rmtree(dest)
    staging = Path(tempfile.mkdtemp(prefix=f".{dest.stem}.", dir=mirrors_root))
    clone = staging / "mirror.git"
    try:
        subprocess.run(["git", "clone", "--mirror", url, str(clone)], check=True)
        clone.replace(dest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return dest


def _task_revisions() -> dict[str, set[str]]:
    parsed = yaml.safe_load(TASKS_FILE.read_text(encoding="utf-8")) or {}
    revisions: dict[str, set[str]] = defaultdict(set)
    for task in parsed.get("tasks", []):
        workspace = task.get("workspace", {})
        source = workspace.get("source")
        revision = workspace.get("ref")
        if source and revision:
            revisions[source].add(revision)
    return dict(revisions)


def _missing_revisions(mirror: Path, revisions: set[str]) -> set[str]:
    if not revisions:
        return set()
    ordered = sorted(revisions)
    probe = subprocess.run(
        ["git", "--git-dir", str(mirror), "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        input="\n".join(ordered) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    lines = probe.stdout.splitlines()
    if len(lines) != len(ordered):
        raise RuntimeError(f"git returned {len(lines)} checks for {len(ordered)} SWE task revisions")
    return {revision for revision, line in zip(ordered, lines) if not line.endswith(" commit")}


def _ensure_task_revisions(mirror: Path, revisions: set[str]) -> None:
    missing = sorted(_missing_revisions(mirror, revisions))
    if missing:
        print(f"  fetching {len(missing)} task revisions omitted by advertised refs", flush=True)
    for start in range(0, len(missing), 50):
        batch = missing[start:start + 50]
        refspecs = [f"{revision}:refs/refactor-platform/tasks/{revision}" for revision in batch]
        subprocess.run(
            ["git", "--git-dir", str(mirror), "fetch", "--no-tags", "origin", *refspecs],
            check=True,
        )
    unresolved = _missing_revisions(mirror, revisions)
    if unresolved:
        sample = ", ".join(sorted(unresolved)[:5])
        raise RuntimeError(f"SWE mirror is missing {len(unresolved)} required task revisions: {sample}")


def _shared_mirrors_root() -> Path:
    import os
    return Path(os.getenv("RP_DATA_DIR", str(Path.home() / "refactor-platform" / "data"))) / "mirrors"


def _install_archive(archive: Path, data_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix=".extract-", dir=data_dir) as tmp:
        staging = Path(tmp)
        with zipfile.ZipFile(archive) as z:
            _safe_extract(z, staging)
        _flatten(staging)
        if not _data_complete(staging):
            raise RuntimeError("SWE-Refactor ZIP has an unsupported layout")

        dataset_dest = data_dir / DATASET
        data_dest = data_dir / "data"
        dataset_dest.unlink(missing_ok=True)
        if data_dest.exists():
            shutil.rmtree(data_dest)
        (staging / DATASET).replace(dataset_dest)
        (staging / "data").replace(data_dest)


def _safe_extract(archive: zipfile.ZipFile, dest: Path) -> None:
    root = dest.resolve()
    for member in archive.infolist():
        target = (dest / member.filename).resolve()
        if target != root and root not in target.parents:
            raise OSError(f"unsafe ZIP entry: {member.filename}")
    archive.extractall(dest)


def _flatten(root: Path) -> None:
    """Normalize the real release to ``pure_refactoring_data.json`` + ``data/``.

    Zenodo nests both beneath ``SWE-Refactor/`` and places RefactoringMiner in
    ``code/data/tools``. Only those runtime inputs are retained.
    """
    release = root / "SWE-Refactor" if (root / "SWE-Refactor").is_dir() else root
    source_data = release / "code" / "data"
    destination_data = root / "data"
    if source_data.is_dir() and source_data != destination_data:
        if destination_data.exists():
            shutil.rmtree(destination_data)
        source_data.rename(destination_data)

    source_dataset = release / DATASET
    destination_dataset = root / DATASET
    if source_dataset.is_file() and source_dataset != destination_dataset:
        destination_dataset.unlink(missing_ok=True)
        source_dataset.rename(destination_dataset)

    if release != root:
        shutil.rmtree(release, ignore_errors=True)
    shutil.rmtree(root / "__MACOSX", ignore_errors=True)


if __name__ == "__main__":
    bootstrap(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data")
