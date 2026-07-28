"""What every rendered prompt must say, and what a prompt file may be called.

Both assertions come from observed damage: an agent that could not find the code
because nothing told it where the repository was, and prompt assets whose names
leaked the templating library's build suffix.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

PLUGINS = Path(__file__).resolve().parents[2] / "plugins"


def test_a_rendered_prompt_states_the_repository_root_first():
    from app.execution.taskloop import _workspace_preamble

    session = SimpleNamespace(workspace=Path("/data/outputs/runs/r1/tasks/t1/workspace"))
    text = _workspace_preamble(session)
    assert text.startswith("Repository root: /data/outputs/runs/r1/tasks/t1/workspace")
    assert "relative to it" in text


def test_no_shipped_prompt_file_carries_a_template_build_suffix():
    """`.j2` is a detail of the templating library, not a name for a document.

    Files under a benchmark's `data/` belong to the repositories it checks out
    and are none of the platform's business.
    """
    offenders = [
        path.relative_to(PLUGINS).as_posix()
        for path in PLUGINS.rglob("prompts/*")
        if path.is_file() and (path.name.endswith(".j2") or "baseline_prompt" in path.name)
    ]
    assert offenders == []


def test_every_declared_prompt_template_exists_and_is_reachable():
    """A manifest naming a template the resolver cannot open fails at run time,
    on the first task, after the workspace has already been prepared."""
    import yaml

    from app.api.prompts import _SUFFIXES

    for manifest_path in sorted(PLUGINS.glob("benchmarks/*/plugin.yaml")):
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        declared = (manifest.get("prompt") or {}).get("template")
        if not declared:
            continue
        template = manifest_path.parent / declared
        assert template.is_file(), f"{manifest_path.parent.name} declares missing {declared}"
        assert template.name.endswith(_SUFFIXES), f"{declared} is not a listed prompt suffix"


def test_the_preamble_resolves_a_path_the_task_writes_relative_to_a_subdirectory(tmp_path):
    """RefactorBench asks for `requests/utils.py` in a checkout that keeps that
    file under `src/`. Every agent used to discover this by failed reads: one
    recorded run spent four turns on paths that do not exist."""
    from app.execution.taskloop import _workspace_preamble

    (tmp_path / "src" / "requests").mkdir(parents=True)
    (tmp_path / "src" / "requests" / "utils.py").write_text("def select_proxy():\n    ...\n",
                                                            encoding="utf-8")
    task = SimpleNamespace(
        instructions="Please modify the 'select_proxy' function in the file 'requests/utils.py' "
                     "to include an additional parameter named 'log'.",
        params={"cwd_hint": "src"})
    text = _workspace_preamble(SimpleNamespace(workspace=tmp_path), task,
                               SimpleNamespace(pathsRelativeTo="params.cwd_hint"))
    assert "`requests/utils.py` is `src/requests/utils.py`" in text


def test_the_preamble_says_nothing_extra_when_the_paths_already_resolve(tmp_path):
    from app.execution.taskloop import _workspace_preamble

    (tmp_path / "requests").mkdir()
    (tmp_path / "requests" / "utils.py").write_text("x = 1\n", encoding="utf-8")
    task = SimpleNamespace(instructions="modify 'requests/utils.py'", params={"cwd_hint": "src"})
    text = _workspace_preamble(SimpleNamespace(workspace=tmp_path), task,
                               SimpleNamespace(pathsRelativeTo="params.cwd_hint"))
    assert "relative to" in text and "src/" not in text


def test_refactorbench_declares_where_its_instructions_write_paths():
    """The task data already recorded the directory and only the scoring step
    read it, which is why the prompt disagreed with the checkout."""
    import yaml

    manifest = yaml.safe_load(
        (PLUGINS / "benchmarks" / "refbench" / "plugin.yaml").read_text(encoding="utf-8"))
    assert manifest["prompt"]["pathsRelativeTo"] == "params.cwd_hint"
    verify = {stage["preset"] if isinstance(stage, dict) else stage
              for stage in manifest["evaluation"]["verify"]}
    assert "python_tests" in verify, "the same hint drives the scoring step"
