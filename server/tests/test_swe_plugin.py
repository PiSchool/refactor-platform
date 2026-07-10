from __future__ import annotations

import json
import re
import sys
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
    res = swe._prepare_candidate(ctx, {})
    assert res.ok is True
    rm = ctx.shared["rm_args"]
    assert rm[0] == "-scr" and rm[1] == "src/A.java" and rm[-1] == "Extract Method"
    assert Path(rm[3]).read_text().startswith("package p;")


def test_prepare_fails_when_target_absent(swe, tmp_path):
    ws = tmp_path / "ws"; ws.mkdir()
    res = swe._prepare_candidate(_ctx(ws, PARAMS, swe._DATA), {})
    assert res.ok is False and res.reason == "apply_failed"


def test_prepare_move_reads_destination(swe, tmp_path):
    ws = tmp_path / "ws"; (ws / "dst").mkdir(parents=True)
    (ws / "dst" / "B.java").write_text(AFTER)
    params = {**PARAMS, "refactoringType": "Move Method", "filePathAfter": "dst/B.java"}
    ctx = _ctx(ws, params, swe._DATA)
    res = swe._prepare_candidate(ctx, {})
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
    from app.evaluation.presets import java_build

    task = type("Task", (), {"params": {"cmd": "mvn -Dtest='!A"}})()
    ctx = type("Ctx", (), {"workspace": tmp_path, "task": task})()
    res = java_build.run(ctx, {"command_from": "params.cmd"})
    assert res.ok is False
    assert res.reason == "malformed_build_command"
    assert "unrunnable build command" in res.message


def _eval_ctx(tmp_path, params, workspace_files):
    task = type("Task", (), {"params": params})()
    ws = tmp_path / "ws"
    for rel, body in workspace_files.items():
        f = ws / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    return type("Ctx", (), {"task": task, "workspace": ws, "data_root": tmp_path, "shared": {}})()


def test_codebleu_scores_the_workspace_file_against_the_reference(swe, tmp_path, monkeypatch):
    """The agent's file, not an answer envelope, is what gets scored."""
    java = "class A { void f() { int x = 1; g(x); } void g(int y) {} }"
    row = {"uniqueId": "u1", "sourceCodeAfterForWhole": java}
    monkeypatch.setattr(swe, "_row", lambda *a, **k: row)

    ctx = _eval_ctx(tmp_path, {"uniqueId": "u1", "filePathBefore": "A.java"}, {"A.java": java})
    res = swe._codebleu(ctx, {})
    assert res.ok is True
    assert res.outputs["codebleu"] == 1.0          # identical file scores 1.0
    assert "CodeBLEU 1.000" in res.message

    # an unrelated file scores far lower
    ctx2 = _eval_ctx(tmp_path / "b", {"uniqueId": "u1", "filePathBefore": "A.java"},
                     {"A.java": "class B { void zzz() { System.out.println(42); } }"})
    assert swe._codebleu(ctx2, {}).outputs["codebleu"] < 0.5


def test_codebleu_never_fails_a_run(swe, tmp_path, monkeypatch):
    """A missing candidate or a broken scorer must not turn into a task failure."""
    monkeypatch.setattr(swe, "_row", lambda *a, **k: {"sourceCodeAfterForWhole": "class A {}"})
    ctx = _eval_ctx(tmp_path, {"filePathBefore": "missing.java"}, {})
    res = swe._codebleu(ctx, {})
    assert res.ok is True and res.outputs == {}
