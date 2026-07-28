from __future__ import annotations

from pathlib import Path

import pytest

from app.catalog.sdk import EvalContext, SessionInfo, TaskDef, WorkspaceSpec
# imported under another name: the runner collects any module-level `test_*`
from app.catalog.reports import counts as parse_counts
from app.catalog.reports import counts_message
from app.evaluation import expressions
from tests.helpers import metric


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


def test_baseline_text_separates_a_new_file_from_an_unreadable_workspace(tmp_path):
    """A stage has to tell "the agent created this" from "git could not answer".

    Both used to arrive as an empty string, and a metric comparing against it
    reported a correct refactoring as no refactoring at all.
    """
    import subprocess

    ws = tmp_path / "ws"
    (ws / "pkg").mkdir(parents=True)
    (ws / "pkg" / "kept.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "add", "-A"], cwd=ws, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "baseline"], cwd=ws, check=True)
    (ws / "pkg" / "kept.py").write_text("x = 2\n", encoding="utf-8")
    (ws / "pkg" / "added.py").write_text("y = 1\n", encoding="utf-8")

    def context(workspace):
        return EvalContext(task=_task(), workspace=workspace,
                           artifacts_dir=tmp_path / "art", data_root=tmp_path / "data",
                           session=None, diff_text="", advisory=False)

    assert context(ws).baseline_text("pkg/kept.py") == "x = 1\n"
    assert context(ws).baseline_text("pkg/added.py") == ""

    without_git = tmp_path / "no-repo"
    (without_git / "pkg").mkdir(parents=True)
    (without_git / "pkg" / "kept.py").write_text("x = 1\n", encoding="utf-8")
    assert context(without_git).baseline_text("pkg/kept.py") is None


def test_python_tests_pass_and_fail(tmp_path):
    python_tests = metric("python_tests")

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
    res = python_tests.measure(ctx, {"test_from": "params.test_file", "sys_path_repo_root": True})
    assert res.ok is True
    assert res.name == "python_tests", "the recorded stage is the metric's id"


    ws2 = tmp_path / "ws2"
    ws2.mkdir()
    (ws2 / "mod.py").write_text("def add(a, b):\n    return a - b\n")
    ctx2 = EvalContext(task=_task({"test_file": "tests/t_mod.py"}), workspace=ws2,
                       artifacts_dir=tmp_path, data_root=data, session=SessionInfo(),
                       diff_text="x", advisory=False)
    res2 = python_tests.measure(ctx2, {"test_from": "params.test_file", "sys_path_repo_root": True})
    assert res2.ok is False
    assert res2.reason == "test_failed"


def test_workspace_changed():
    workspace_changed = metric("workspace_changed")

    ctx = EvalContext(task=_task(), workspace=Path("/x"), artifacts_dir=Path("/x"),
                      data_root=Path("/x"), session=None, diff_text="", advisory=False)
    assert workspace_changed.measure(ctx, {}).ok is False
    ctx.diff_text = "diff --git a b"
    assert workspace_changed.measure(ctx, {}).ok is True


def test_java_build_passes_env_with_utf8_locale(tmp_path, monkeypatch):
    """Regression: the computed env (JAVA_HOME + UTF-8 locale) must actually
    reach the subprocess. It once did not, so per-task JDK selection had no
    effect and an *unmodified* checkout failed charset tests, blaming the agent.
    java.io.tmpdir must NOT be overridden — suites assert on its value."""
    import sys

    from app.catalog import workspace_commands
    from app.catalog.sdk import EvalContext, TaskDef, WorkspaceSpec

    java_build = metric("java_build").impl
    seen = {}

    class _Recorded:
        returncode = 0
        pid = 2 ** 30

        def __init__(self, cmd, **kw):
            seen["cmd"] = cmd
            seen["env"] = kw.get("env")
            seen["own_group"] = kw.get("start_new_session")

        def communicate(self, timeout=None):
            return "", ""

    monkeypatch.setattr(workspace_commands.subprocess, "Popen", _Recorded)
    task = TaskDef("t", "t", "java", WorkspaceSpec("git", "u", "s"), "i", {})
    ctx = EvalContext(task=task, workspace=tmp_path, artifacts_dir=tmp_path,
                      data_root=tmp_path, session=None, diff_text="", advisory=False)

    plugin = sys.modules[type(java_build).__module__]
    outcome = plugin._build(ctx, "mvn -B test", "17", "/tmp/m2", None)
    assert outcome.ok
    assert outcome.timed_out is False
    env = seen["env"]
    assert env is not None, "env must be passed to the subprocess (JAVA_HOME had no effect once)"
    assert env["LANG"].endswith("UTF-8") and env["LC_ALL"].endswith("UTF-8")
    assert "-Dmaven.repo.local=" in seen["cmd"]
    assert "-Djava.io.tmpdir=" not in seen["cmd"], "overriding java.io.tmpdir breaks FilesUncheckTest"
    assert seen["own_group"] is True, "a timeout must be able to kill the whole build tree"


def test_java_build_normalizes_legacy_jdk_major():
    """The dataset writes Java 8 as '1.8'; JDK_1.8_HOME does not exist, so the
    build silently fell back to the default JDK for 105 tasks."""
    import sys

    plugin = sys.modules[type(metric("java_build").impl).__module__]

    assert plugin.normalize_major("1.8") == "8"
    assert plugin.normalize_major("8") == "8"
    assert plugin.normalize_major("17") == "17"
    assert plugin.normalize_major(21) == "21"


def _spec(verify, passed):
    from app.catalog.manifest import EvaluationSpec, Stage
    return EvaluationSpec(verify=[Stage(preset=p, config=c) for p, c in verify], passed=passed)


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


def test_an_operator_can_add_an_installed_metric_the_benchmark_does_not_ship():
    """Adding a measurement to a pipeline needs no plugin edit.

    A benchmark's manifest is where its author put the pipeline; an operator
    scoring the same tasks differently should not have to fork it.
    """
    from app.evaluation.engine import effective_pipeline

    installed = metric("workspace_changed").id       # loads the shipped metrics
    ev = _spec([("a", {})], "a")
    verify, _ = effective_pipeline(
        ev, {"verify": [{"preset": installed, "config": {"x": 1}, "enabled": True}]})
    assert verify == [("a", {}), (installed, {"x": 1})]


def test_a_stage_naming_a_metric_that_is_not_installed_is_dropped():
    """An override outlives the plugin it was written against.

    Keeping the stage would fail every task in the run on a missing metric, so a
    stale reference is ignored and the rest of the pipeline still runs.
    """
    from app.evaluation.engine import effective_pipeline

    ev = _spec([("a", {})], "a")
    verify, _ = effective_pipeline(ev, {"verify": [{"preset": "ghost_metric", "enabled": True}]})
    assert verify == [("a", {})]


def test_test_counts_parses_unittest_pytest_and_surefire():
    """'5/5 tests passed' beats 'Tests passed.' — parse the real runners."""
    # unittest, the shape refbench actually emits
    unittest_fail = "Ran 5 tests in 0.012s\n\nFAILED (failures=2)\n"
    assert parse_counts(unittest_fail) == (3, 5)
    assert counts_message(unittest_fail, False) == "3/5 tests passed."

    unittest_ok = "Ran 5 tests in 0.011s\n\nOK\n"
    assert parse_counts(unittest_ok) == (5, 5)

    assert parse_counts("Ran 4 tests in 1s\n\nFAILED (failures=1, errors=1)\n") == (2, 4)

    # maven surefire — the aggregate line wins over per-class lines
    surefire = ("Tests run: 55, Failures: 2, Errors: 0, Skipped: 1\n"
                "Tests run: 2032, Failures: 0, Errors: 3, Skipped: 15\n")
    assert parse_counts(surefire) == (2029, 2032)

    # pytest
    assert parse_counts("= 3 failed, 5 passed, 1 skipped in 0.5s =") == (5, 8)

    # nothing to parse (e.g. a compile error)
    assert parse_counts("BUILD FAILURE\ncannot find symbol\n") is None
    assert counts_message("", True) == "Tests passed."


def test_workspace_changed_reports_what_changed():
    """An empty check message tells a reviewer nothing."""
    from app.catalog.sdk import EvalContext

    workspace_changed = metric("workspace_changed")
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1,2 @@\n-x = 1\n+x = 2\n+y = 3\n"
        "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-z = 0\n+z = 1\n"
    )
    ctx = EvalContext(task=_task(), workspace=Path("/x"), artifacts_dir=Path("/x"),
                      data_root=Path("/x"), session=None, diff_text=diff, advisory=False)
    res = workspace_changed.measure(ctx, {})
    assert res.ok is True
    assert res.message == "2 files changed, +3 −2."

    ctx.diff_text = ""
    assert workspace_changed.measure(ctx, {}).ok is False


def test_stage_outputs_are_carried_into_details(tmp_path, monkeypatch):
    """Test counts must reach the CSV/UI as data, not as English to re-parse."""
    from app.catalog.sdk import EvalContext, StageResult
    from app.evaluation import engine

    from app.catalog.manifest import EvaluationSpec
    from app.catalog.sdk import EvaluationPlugin
    from app.evaluation import registry

    class _Loaded:
        hooks = type("H", (), {"evaluate": lambda self, ctx: None})()
        manifest = type("M", (), {"evaluation": EvaluationSpec(
            verify=["python_tests"], passed="python_tests")})()

    class _Stub(EvaluationPlugin):
        def measure(self, ctx, config):
            return StageResult(ok=True, message="5/5 tests passed.",
                               outputs={"testsPassed": 5, "testsTotal": 5})

    # the metric table is shared process-wide: replacing an entry outright left
    # every later test in the session looking at this stub
    monkeypatch.setitem(
        registry._METRICS, "python_tests",
        registry.Metric(id="python_tests", impl=_Stub(), plugin_dir=tmp_path))
    ctx = EvalContext(task=_task(), workspace=tmp_path, artifacts_dir=tmp_path,
                      data_root=tmp_path, session=None, diff_text="d", advisory=False)
    out = engine.evaluate(_Loaded(), ctx)
    assert out.details["python_tests"]["testsPassed"] == 5
    assert out.details["python_tests"]["testsTotal"] == 5
    assert out.details["python_tests"]["ok"] is True


def test_javac_error_count_is_not_read_as_a_test_count():
    """Maven prints "[INFO] 14 errors" on a compile failure; that is not 14 tests."""
    log = (
        "[ERROR] TestUtils.java:[71,5] illegal start of expression\n"
        "[INFO] 14 errors \n"
        "[INFO] BUILD FAILURE\n"
        "[ERROR] Failed to execute goal ... Compilation failure: Compilation failure:\n"
    )
    assert parse_counts(log) is None
    assert counts_message(log, ok=False) == "Compilation failed; no tests ran."


def test_surefire_and_pytest_counts_still_parse():
    assert parse_counts("[WARNING] Tests run: 2032, Failures: 0, Errors: 0, Skipped: 15") == (2032, 2032)
    assert parse_counts("Tests run: 10, Failures: 2, Errors: 1, Skipped: 0") == (7, 10)
    assert parse_counts("===== 3 failed, 5 passed, 1 skipped in 0.51s =====") == (5, 8)
    assert parse_counts("5 passed in 0.12s") == (5, 5)
    # a stray sentence must not become a test count
    assert parse_counts("we saw 14 errors while linting") is None


# --------------------------------------------------------------------------- #
# a build must not outlive its task
# --------------------------------------------------------------------------- #

def test_gradle_builds_run_without_a_daemon():
    """A leaked Gradle daemon outlives the task and holds the machine.

    One deployment was found with a daemon alive 54 minutes after its task had
    finished, plus eight unreaped JVMs, while later tasks queued behind the same
    CPU. A task that asks for a daemon explicitly still gets one.
    """
    import sys

    plugin = sys.modules[type(metric("java_build").impl).__module__]
    without = plugin.without_gradle_daemon

    assert without("./gradlew clean test") == "./gradlew --no-daemon clean test"
    assert without("gradle test") == "gradle --no-daemon test"
    assert without("mvn -q -B test") == "mvn -q -B test"
    assert without("./gradlew --daemon test") == "./gradlew --daemon test"


def test_a_timed_out_build_kills_the_whole_process_tree(tmp_path):
    """The shell was killed and its children kept building.

    The build runs in its own process group, so the timeout reaches every
    process it started.
    """
    import os
    import time
    import types

    import sys

    plugin = sys.modules[type(metric("java_build").impl).__module__]

    pidfile = tmp_path / "child.pid"
    command = f"sleep 60 & echo $! > {pidfile}; wait"

    outcome = plugin._build(
        types.SimpleNamespace(workspace=tmp_path), command, "", str(tmp_path / "m2"), 1.0
    )

    assert (outcome.ok, outcome.timed_out) == (False, True)
    child = int(pidfile.read_text().strip())
    for _ in range(50):
        try:
            os.kill(child, 0)
        except (ProcessLookupError, PermissionError):
            break
        time.sleep(0.1)
    else:                                                   # pragma: no cover
        os.kill(child, 9)
        raise AssertionError(f"the build's child {child} survived the timeout")
