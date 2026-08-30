from __future__ import annotations

import json
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import pytest

SWE = Path(__file__).resolve().parents[2] / "plugins" / "benchmarks" / "swe"

ROW = {
    "uniqueId": "u1", "commitId": "c1", "projectName": "commons-io",
    "type": "Extract Method", "filePathBefore": "src/A.java", "filePathAfter": "src/A.java",
    "sourceCodeBeforeRefactoring": "void f() { a(); b(); }",
    "sourceCodeBeforeForWhole": "class A {}",
    "methodNameBefore": "f", "classNameBefore": "A",
    "sourceCodeAfterRefactoring": "SECRET_ANSWER", "diffSourceCode": "SECRET_DIFF",
    "compileCommand": "mvn test", "compileJDK": "17",
}


def _bootstrap_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("swe_bootstrap_under_test", SWE / "data_bootstrap.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_download_rejects_bad_zip_without_overwriting_existing_archive(tmp_path, monkeypatch):
    mod = _bootstrap_module()
    dest = tmp_path / "SWE-Refactor.zip"
    dest.write_bytes(b"known-good-placeholder")

    class Response(BytesIO):
        headers = {"Content-Length": "9"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    monkeypatch.setattr(mod.urllib.request, "urlopen", lambda *_args, **_kwargs: Response(b"not a zip"))

    with pytest.raises(OSError, match="ZIP integrity"):
        mod._download("https://example.invalid/swe.zip", dest, attempts=1)
    assert dest.read_bytes() == b"known-good-placeholder"
    assert not list(tmp_path.glob("*.part"))


def test_flatten_normalizes_the_real_zenodo_release_layout(tmp_path):
    mod = _bootstrap_module()
    release = tmp_path / "SWE-Refactor"
    tools = release / "code" / "data" / "tools" / "RefactoringMiner-3.0.10" / "bin"
    tools.mkdir(parents=True)
    (tools / "RefactoringMiner").write_text("#!/bin/sh\n", encoding="utf-8")
    (release / "code" / "data" / "commons-io").mkdir()
    (release / "pure_refactoring_data.json").write_text("[]\n", encoding="utf-8")

    mod._flatten(tmp_path)

    assert (tmp_path / "pure_refactoring_data.json").is_file()
    assert (tmp_path / "data" / "tools" / "RefactoringMiner-3.0.10" / "bin" / "RefactoringMiner").is_file()
    assert not (tmp_path / "SWE-Refactor").exists()


def test_task_revision_fetch_anchors_commits_missing_from_the_mirror(tmp_path):
    mod = _bootstrap_module()
    source = tmp_path / "source"
    source.mkdir()

    def git(*args, cwd=source):
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

    git("init", "--initial-branch=main")
    git("config", "user.email", "tests@example.invalid")
    git("config", "user.name", "Tests")
    (source / "file.txt").write_text("one\n", encoding="utf-8")
    git("add", "file.txt")
    git("commit", "-m", "one")
    first = git("rev-parse", "HEAD")

    mirror = tmp_path / "mirror.git"
    subprocess.run(["git", "clone", "--mirror", str(source), str(mirror)], check=True, capture_output=True)
    (source / "file.txt").write_text("two\n", encoding="utf-8")
    git("commit", "-am", "two")
    second = git("rev-parse", "HEAD")

    assert mod._missing_revisions(mirror, {first, second}) == {second}
    mod._ensure_task_revisions(mirror, {first, second})
    assert mod._missing_revisions(mirror, {first, second}) == set()
    anchored = subprocess.run(
        ["git", "--git-dir", str(mirror), "rev-parse", f"refs/refactor-platform/tasks/{second}"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert anchored == second


@pytest.fixture()
def swe(tmp_path, monkeypatch):
    import importlib.util

    sys.path.insert(0, str(SWE))
    spec = importlib.util.spec_from_file_location("swe_plugin_under_test", SWE / "plugin.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # point the dataset lookup at a fixture row
    data = tmp_path / "data"
    data.mkdir()
    (data / "pure_refactoring_data.json").write_text(json.dumps([ROW]))
    monkeypatch.setattr(mod, "PLUGIN_DIR", SWE)
    mod._rows_by_id.cache_clear()
    mod._DATA = data
    return mod


def _ctx(tmp_path, params, data_root):
    from app.catalog.sdk import EvalContext, SessionInfo, TaskDef, WorkspaceSpec

    task = TaskDef("commons-io/u1", "t", "java", WorkspaceSpec("git", "url", "sha"), "do", params)
    return EvalContext(task=task, workspace=tmp_path, artifacts_dir=tmp_path,
                       data_root=data_root, session=SessionInfo(), diff_text="d", advisory=False)


AFTER = "package p;\nclass A {\n    void extracted() {}\n    void f() { extracted(); }\n}\n"
PARAMS = {"project": "commons-io", "refactoringType": "Extract Method", "uniqueId": "u1",
          "filePathBefore": "src/A.java", "filePathAfter": "src/A.java",
          "compileCommand": "mvn test", "compileJDK": "17"}


def test_prepare_single_file_reads_workspace(swe, tmp_path):
    ws = tmp_path / "ws"; (ws / "src").mkdir(parents=True)
    (ws / "src" / "A.java").write_text(AFTER)
    ctx = _ctx(ws, PARAMS, swe._DATA)
    res = swe.Plugin().prepare(ctx)
    assert res.ok is True
    rm = ctx.shared["rm_args"]
    assert rm[0] == "-scr" and rm[1] == "src/A.java" and rm[-1] == "Extract Method"
    assert Path(rm[3]).read_text().startswith("package p;")
    # the same step publishes what the similarity metric compares, so that metric
    # needs to know nothing about this benchmark or its dataset
    assert ctx.shared["candidate_path"] == str(ws / "src" / "A.java")
    assert "reference_text" in ctx.shared


def test_prepare_fails_when_target_absent(swe, tmp_path):
    ws = tmp_path / "ws"; ws.mkdir()
    res = swe.Plugin().prepare(_ctx(ws, PARAMS, swe._DATA))
    assert res.ok is False and res.reason == "apply_failed"


def test_prepare_move_reads_destination(swe, tmp_path):
    ws = tmp_path / "ws"; (ws / "dst").mkdir(parents=True)
    (ws / "dst" / "B.java").write_text(AFTER)
    params = {**PARAMS, "refactoringType": "Move Method", "filePathAfter": "dst/B.java"}
    ctx = _ctx(ws, params, swe._DATA)
    res = swe.Plugin().prepare(ctx)
    assert res.ok is True
    rm = ctx.shared["rm_args"]
    assert rm[0] == "-spr" and rm[3] == "dst/B.java" and rm[-1] == "Move Method"


def test_build_prompt_uses_type_template_and_hides_answers(swe, tmp_path, monkeypatch):
    from app.catalog.sdk import SessionCtx, SetupProfile, TaskDef, WorkspaceSpec

    monkeypatch.setattr(swe, "_row", lambda task, d: ROW)
    ws = tmp_path / "ws"; ws.mkdir()
    task = TaskDef("commons-io/u1", "t", "java", WorkspaceSpec("git", "u", "s"), "do", PARAMS)
    ctx = SessionCtx(run_id="r", run_task_id="rt", session_id="s", task=task, workspace=ws,
                     artifacts_dir=ws, prompt_path=ws / "p", config_dir=ws,
                     model="m", setup=SetupProfile("s1", "S1", ""), requested_env={})
    prompt = swe.Plugin().build_prompt(task, ctx)
    assert "expert software engineer" in prompt          # POC task description
    assert "Code to be Refactored:" in prompt            # POC section headers
    assert "Class content:" in prompt
    assert "Extract Method" in prompt
    assert "SECRET_ANSWER" not in prompt
    assert "SECRET_DIFF" not in prompt
    # every template placeholder was substituted
    assert not re.search(r"\{(task_description|code_to_refactor|class_content|"
                         r"refactoring_operation|project_structure|"
                         r"file_path_before_refactoring)\}", prompt)


def test_move_prompt_includes_project_structure(swe, tmp_path, monkeypatch):
    from app.catalog.sdk import SessionCtx, SetupProfile, TaskDef, WorkspaceSpec

    row = {**ROW, "type": "Move Method"}
    monkeypatch.setattr(swe, "_row", lambda task, d: row)
    ws = tmp_path / "ws"; (ws / "src" / "main" / "java").mkdir(parents=True)
    (ws / "src" / "main" / "java" / "Target.java").write_text("class Target {}")
    params = {**PARAMS, "refactoringType": "Move Method", "filePathBefore": "src/main/java/A.java"}
    task = TaskDef("k", "t", "java", WorkspaceSpec("git", "u", "s"), "do", params)
    ctx = SessionCtx(run_id="r", run_task_id="rt", session_id="s", task=task, workspace=ws,
                     artifacts_dir=ws, prompt_path=ws / "p", config_dir=ws,
                     model="m", setup=SetupProfile("s1", "S1", ""), requested_env={})
    prompt = swe.Plugin().build_prompt(task, ctx)
    assert "Project Structure:" in prompt
    assert "src/main/java/Target.java" in prompt


def test_swe_discovers(swe):
    from app.catalog.loader import discover

    reg = discover(SWE.parents[1])
    assert "swe" in reg.benchmarks


def test_repair_command_closes_the_datasets_truncated_exclusion_list():
    """93 commons-io rows ship `-Dtest='!A,!B` with no closing quote; handed to a
    shell it dies with a syntax error that looks like the agent broke the build."""
    import shlex
    sys.path.insert(0, str(SWE))
    from generate_tasks import repair_command

    broken = "mvn clean package -Dtest='!FileUtilsDeleteDirectoryLinuxTestCase,!ObservableInputStreamTest"
    with pytest.raises(ValueError):
        shlex.split(broken)
    assert shlex.split(repair_command(broken))[-1] == (
        "-Dtest=!FileUtilsDeleteDirectoryLinuxTestCase,!ObservableInputStreamTest"
    )
    good = "mvn -U clean package -pl '!guava-gwt' -am"
    assert repair_command(good) == good


def test_java_build_reports_malformed_command_as_data_defect_not_build_failure(tmp_path):
    from tests.helpers import metric

    ctx = _eval_ctx(tmp_path, {"cmd": "mvn -Dtest='!A"}, {})
    res = metric("java_build").measure(ctx, {"command_from": "params.cmd"})
    assert res.ok is False
    assert res.reason == "malformed_build_command"
    assert "unrunnable build command" in res.message


def _eval_ctx(tmp_path, params, workspace_files):
    from app.catalog.sdk import EvalContext, TaskDef, WorkspaceSpec

    ws = tmp_path / "ws"
    ws.mkdir(parents=True, exist_ok=True)
    for rel, body in workspace_files.items():
        f = ws / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    task = TaskDef("commons-io/u1", "t", "java", WorkspaceSpec("git", "u", "s"), "do", params)
    return EvalContext(task=task, workspace=ws, artifacts_dir=tmp_path, data_root=tmp_path,
                       session=None, diff_text="", advisory=False)


def _prepared(swe, tmp_path, monkeypatch, java, workspace_files, params=None):
    """A context the benchmark has prepared, which is what a metric receives."""
    row = {"uniqueId": "u1", "sourceCodeBeforeForWhole": "class A {}",
           "sourceCodeAfterForWhole": java}
    monkeypatch.setattr(swe, "_row", lambda *a, **k: row)
    ctx = _eval_ctx(tmp_path, {"uniqueId": "u1", "filePathBefore": "A.java",
                               "filePathAfter": "A.java", "refactoringType": "Extract Method",
                               **(params or {})}, workspace_files)
    swe.Plugin().prepare(ctx)
    return ctx


def test_codebleu_scores_the_workspace_file_against_what_the_benchmark_published(
        swe, tmp_path, monkeypatch):
    """The agent's file, not an answer envelope, is what gets scored.

    The metric knows nothing about this dataset: the benchmark's preparation step
    publishes the reference and the candidate, and the same metric serves any
    benchmark that publishes them.
    """
    from tests.helpers import metric

    java = "class A { void f() { int x = 1; g(x); } void g(int y) {} }"
    codebleu = metric("codebleu")

    ctx = _prepared(swe, tmp_path, monkeypatch, java, {"A.java": java})
    res = codebleu.measure(ctx, {"language": "java"})
    assert res.ok is True
    assert res.name == "codebleu"
    assert res.outputs["codebleu"] == 1.0          # identical file scores 1.0
    assert "CodeBLEU 1.000" in res.message

    # an unrelated file scores far lower
    other = _prepared(swe, tmp_path / "b", monkeypatch, java,
                      {"A.java": "class B { void zzz() { System.out.println(42); } }"})
    assert codebleu.measure(other, {"language": "java"}).outputs["codebleu"] < 0.5


def test_codebleu_never_fails_a_run(swe, tmp_path, monkeypatch):
    """A missing candidate or a broken scorer must not turn into a task failure.

    It records a number; the verdict belongs to the gates.
    """
    from tests.helpers import metric

    assert metric("codebleu").spec.gates is False
    ctx = _eval_ctx(tmp_path, {"filePathBefore": "missing.java"}, {})
    res = metric("codebleu").measure(ctx, {})
    assert res.ok is True and res.outputs == {}
