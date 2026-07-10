from __future__ import annotations

from pathlib import Path

import pytest

from app.catalog.sdk import EvalContext, SessionInfo, TaskDef, WorkspaceSpec
from app.evaluation import expressions


def test_expression_and_or_not():
    assert expressions.evaluate("a and b", {"a": True, "b": True}) is True
    assert expressions.evaluate("a and b", {"a": True, "b": False}) is False
    assert expressions.evaluate("a or b", {"a": False, "b": True}) is True
    assert expressions.evaluate("not a", {"a": False}) is True


def test_expression_unknown_token_rejected():
    with pytest.raises(ValueError):
        expressions.evaluate("a and c", {"a": True})


def test_expression_empty_means_all():
    assert expressions.evaluate("", {"a": True, "b": True}) is True
    assert expressions.evaluate("", {"a": True, "b": False}) is False


def _task(params=None):
    return TaskDef(task_key="t", title="t", language="python",
                   workspace=WorkspaceSpec(type="snapshot", source="repo"),
                   instructions="i", params=params or {})


def test_python_tests_pass_and_fail(tmp_path):
    from app.evaluation.presets import python_tests

    # workspace with a module + a test file living outside the repo (data_root)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "mod.py").write_text("def add(a, b):\n    return a + b\n")
    data = tmp_path / "data"
    (data / "tests").mkdir(parents=True)
    test_file = data / "tests" / "t_mod.py"
    test_file.write_text(
        "import sys, unittest\n"
        "from mod import add\n"
        "class T(unittest.TestCase):\n"
        "    def test(self):\n"
        "        assert add(1, 2) == 3\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    )
    ctx = EvalContext(task=_task({"test_file": "tests/t_mod.py"}), workspace=ws,
                      artifacts_dir=tmp_path, data_root=data, session=SessionInfo(),
                      diff_text="x", advisory=False)
    res = python_tests.run(ctx, {"test_from": "params.test_file", "sys_path_repo_root": True})
    assert res.ok is True

    ws2 = tmp_path / "ws2"
    ws2.mkdir()
    (ws2 / "mod.py").write_text("def add(a, b):\n    return a - b\n")
    ctx2 = EvalContext(task=_task({"test_file": "tests/t_mod.py"}), workspace=ws2,
                       artifacts_dir=tmp_path, data_root=data, session=SessionInfo(),
                       diff_text="x", advisory=False)
    res2 = python_tests.run(ctx2, {"test_from": "params.test_file", "sys_path_repo_root": True})
    assert res2.ok is False
    assert res2.reason == "test_failed"


def test_workspace_changed():
    from app.evaluation.presets import workspace_changed

    ctx = EvalContext(task=_task(), workspace=Path("/x"), artifacts_dir=Path("/x"),
                      data_root=Path("/x"), session=None, diff_text="", advisory=False)
    assert workspace_changed.run(ctx, {}).ok is False
    ctx.diff_text = "diff --git a b"
    assert workspace_changed.run(ctx, {}).ok is True


def test_java_build_passes_env_with_utf8_locale(tmp_path, monkeypatch):
    """Regression: the computed env (JAVA_HOME + UTF-8 locale) must actually
    reach the subprocess. It once did not, so per-task JDK selection had no
    effect and an *unmodified* checkout failed charset tests, blaming the agent.
    java.io.tmpdir must NOT be overridden — suites assert on its value."""
    import subprocess as sp

    from app.catalog.sdk import EvalContext, TaskDef, WorkspaceSpec
    from app.evaluation.presets import java_build

    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        seen["env"] = kw.get("env")
        return sp.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(java_build.subprocess, "run", fake_run)
    task = TaskDef("t", "t", "java", WorkspaceSpec("git", "u", "s"), "i", {})
    ctx = EvalContext(task=task, workspace=tmp_path, artifacts_dir=tmp_path,
                      data_root=tmp_path, session=None, diff_text="", advisory=False)

    ok, _ = java_build._build(ctx, "mvn -B test", "17", "/tmp/m2")
    assert ok
    env = seen["env"]
    assert env is not None, "env must be passed to the subprocess (JAVA_HOME had no effect once)"
    assert env["LANG"].endswith("UTF-8") and env["LC_ALL"].endswith("UTF-8")
    assert "-Dmaven.repo.local=" in seen["cmd"]
    assert "-Djava.io.tmpdir=" not in seen["cmd"], "overriding java.io.tmpdir breaks FilesUncheckTest"


def test_java_build_normalizes_legacy_jdk_major():
    """The dataset writes Java 8 as '1.8'; JDK_1.8_HOME does not exist, so the
    build silently fell back to the default JDK for 105 tasks."""
    from app.evaluation.presets.java_build import _normalize_major

    assert _normalize_major("1.8") == "8"
    assert _normalize_major("8") == "8"
    assert _normalize_major("17") == "17"
    assert _normalize_major(21) == "21"


def _spec(verify, passed):
    from app.catalog.manifest import EvaluationSpec, VerifyStage
    return EvaluationSpec(verify=[VerifyStage(preset=p, config=c) for p, c in verify], passed=passed)


def test_effective_pipeline_without_override_is_the_shipped_one():
    from app.evaluation.engine import effective_pipeline

    ev = _spec([("a", {"x": 1}), ("b", {})], "a and b")
    verify, passed = effective_pipeline(ev, None)
    assert verify == [("a", {"x": 1}), ("b", {})]
    assert passed == "a and b"


def test_effective_pipeline_merges_config_disables_stage_and_replaces_expression():
    from app.evaluation.engine import effective_pipeline

    ev = _spec([("a", {"x": 1, "y": 2}), ("b", {})], "a and b")
    override = {
        "verify": [{"preset": "a", "config": {"y": 99}, "enabled": True},
                   {"preset": "b", "enabled": False}],
        "passed": "a",
    }
    verify, passed = effective_pipeline(ev, override)
    assert verify == [("a", {"x": 1, "y": 99})]      # merged, not replaced
    assert passed == "a"


def test_effective_pipeline_ignores_stages_the_plugin_does_not_ship():
    """The manifest stays the source of truth for what *can* run."""
    from app.evaluation.engine import effective_pipeline

    ev = _spec([("a", {})], "a")
    verify, _ = effective_pipeline(ev, {"verify": [{"preset": "evil", "enabled": True}]})
    assert verify == [("a", {})]


def test_test_counts_parses_unittest_pytest_and_surefire():
    """'5/5 tests passed' beats 'Tests passed.' — parse the real runners."""
    from app.evaluation.presets._util import counts_message, test_counts

    # unittest, the shape refbench actually emits
    unittest_fail = "Ran 5 tests in 0.012s\n\nFAILED (failures=2)\n"
    assert test_counts(unittest_fail) == (3, 5)
    assert counts_message(unittest_fail, False) == "3/5 tests passed."

    unittest_ok = "Ran 5 tests in 0.011s\n\nOK\n"
    assert test_counts(unittest_ok) == (5, 5)

    assert test_counts("Ran 4 tests in 1s\n\nFAILED (failures=1, errors=1)\n") == (2, 4)

    # maven surefire — the aggregate line wins over per-class lines
    surefire = ("Tests run: 55, Failures: 2, Errors: 0, Skipped: 1\n"
                "Tests run: 2032, Failures: 0, Errors: 3, Skipped: 15\n")
    assert test_counts(surefire) == (2029, 2032)

    # pytest
    assert test_counts("= 3 failed, 5 passed, 1 skipped in 0.5s =") == (5, 8)

    # nothing to parse (e.g. a compile error)
    assert test_counts("BUILD FAILURE\ncannot find symbol\n") is None
    assert counts_message("", True) == "Tests passed."


def test_workspace_changed_reports_what_changed():
    """An empty check message tells a reviewer nothing."""
    from app.catalog.sdk import EvalContext
    from app.evaluation.presets import workspace_changed

    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1,2 @@\n-x = 1\n+x = 2\n+y = 3\n"
        "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-z = 0\n+z = 1\n"
    )
    ctx = EvalContext(task=_task(), workspace=Path("/x"), artifacts_dir=Path("/x"),
                      data_root=Path("/x"), session=None, diff_text=diff, advisory=False)
    res = workspace_changed.run(ctx, {})
    assert res.ok is True
    assert res.message == "2 files changed, +3 −2."

    ctx.diff_text = ""
    assert workspace_changed.run(ctx, {}).ok is False


def test_stage_outputs_are_carried_into_details(tmp_path):
    """Test counts must reach the CSV/UI as data, not as English to re-parse."""
    from app.catalog.sdk import EvalContext, StageResult
    from app.evaluation import engine

    class _Hooks:
        def evaluate(self, ctx): return None
        def stages(self): return {}

    class _Manifest:
        class evaluation:
            capture: list = []
            artifact = None
            verify = [type("V", (), {"preset": "python_tests", "config": {}})()]
            passed = "python_tests"

    class _Loaded:
        hooks = _Hooks()
        manifest = _Manifest()

    def fake_stage(ctx, cfg):
        return StageResult(name="python_tests", ok=True, message="5/5 tests passed.",
                           outputs={"testsPassed": 5, "testsTotal": 5})

    engine.CORE_PRESETS["python_tests"] = type("P", (), {"run": staticmethod(fake_stage)})
    ctx = EvalContext(task=_task(), workspace=tmp_path, artifacts_dir=tmp_path,
                      data_root=tmp_path, session=None, diff_text="d", advisory=False)
    out = engine.evaluate(_Loaded(), ctx)
    assert out.details["python_tests"]["testsPassed"] == 5
    assert out.details["python_tests"]["testsTotal"] == 5
    assert out.details["python_tests"]["ok"] is True


def test_javac_error_count_is_not_read_as_a_test_count():
    """Maven prints "[INFO] 14 errors" on a compile failure; that is not 14 tests."""
    from app.evaluation.presets._util import counts_message, test_counts

    log = (
        "[ERROR] TestUtils.java:[71,5] illegal start of expression\n"
        "[INFO] 14 errors \n"
        "[INFO] BUILD FAILURE\n"
        "[ERROR] Failed to execute goal ... Compilation failure: Compilation failure:\n"
    )
    assert test_counts(log) is None
    assert counts_message(log, ok=False) == "Compilation failed; no tests ran."


def test_surefire_and_pytest_counts_still_parse():
    from app.evaluation.presets._util import test_counts

    assert test_counts("[WARNING] Tests run: 2032, Failures: 0, Errors: 0, Skipped: 15") == (2032, 2032)
    assert test_counts("Tests run: 10, Failures: 2, Errors: 1, Skipped: 0") == (7, 10)
    assert test_counts("===== 3 failed, 5 passed, 1 skipped in 0.51s =====") == (5, 8)
    assert test_counts("5 passed in 0.12s") == (5, 5)
    # a stray sentence must not become a test count
    assert test_counts("we saw 14 errors while linting") is None
