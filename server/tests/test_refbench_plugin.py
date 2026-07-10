from __future__ import annotations

from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "benchmarks" / "refbench"
DATA = PLUGIN / "data"


def test_tasks_yaml_generated_and_shaped():
    import yaml

    tasks = yaml.safe_load((PLUGIN / "tasks.yaml").read_text())["tasks"]
    assert len(tasks) > 0
    modes = {t["params"]["mode"] for t in tasks}
    assert modes == {"base", "lazy", "descriptive"}
    sample = tasks[0]
    assert sample["workspace"]["type"] == "snapshot"
    assert sample["params"]["test_file"].startswith("tests/")
    assert "DONE" not in sample["instructions"]  # DONE lives in the prompt template


@pytest.mark.data
def test_repo_and_test_present_and_runnable(tmp_path):
    """With data bootstrapped, a task's workspace prepares and its test file
    executes (fails on the unmodified repo — proving the harness runs)."""
    import subprocess
    import sys

    import yaml

    if not (DATA / ".ready").exists():
        pytest.skip("refbench data not bootstrapped")
    tasks = yaml.safe_load((PLUGIN / "tasks.yaml").read_text())["tasks"]
    t = next(x for x in tasks if x["params"]["repo"] == "requests_refactor")
    repo_src = DATA / t["workspace"]["source"]
    test_file = DATA / t["params"]["test_file"]
    assert repo_src.is_dir() and test_file.is_file()

    import shutil
    ws = tmp_path / "ws"
    shutil.copytree(repo_src, ws)
    shim = ws / "_r.py"
    shim.write_text(f"import sys; sys.path.insert(0,{str(ws)!r})\n"
                    f"import runpy; runpy.run_path({str(test_file)!r}, run_name='__main__')\n")
    cwd = ws / t["params"]["cwd_hint"] if t["params"]["cwd_hint"] else ws
    proc = subprocess.run([sys.executable, str(shim)], cwd=str(cwd), capture_output=True, text=True, timeout=120)
    assert proc.returncode != 0  # unmodified repo → test fails, harness executed
