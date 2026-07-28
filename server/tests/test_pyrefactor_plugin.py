"""The shipped Python refactoring detector, and its reachability as a metric.

A Python task used to be judged by its tests alone, so a rewrite that happened
to pass scored the same as the refactoring that was requested. These tests fix
what each transformation must be called and prove the metric is reachable as
`pyrefactor` from any benchmark.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).resolve().parents[2] / "plugins" / "evaluation" / "pyrefactor"
PLUGINS = Path(__file__).resolve().parents[2] / "plugins"

BEFORE = '''
class Report:
    def render(self, rows):
        """Doc."""
        total = 0
        for row in rows:
            total += row.value
        header = "n=%d" % len(rows)
        return header + str(total)

    def helper(self, x):
        return x + 1


def legacy(a, b):
    return a * b


def caller():
    return legacy(2, 3)
'''

EXTRACTED = '''
class Report:
    def render(self, rows):
        """Doc."""
        total = self._sum(rows)
        return "n=%d" % len(rows) + str(total)

    def _sum(self, rows):
        total = 0
        for row in rows:
            total += row.value
        return total

    def helper(self, x):
        return x + 1


def legacy(a, b):
    return a * b


def caller():
    return legacy(2, 3)
'''


def pyrefactor():
    """The metric as a deployment resolves it: by the name of its directory."""
    from tests.helpers import metric

    return metric("pyrefactor")


def _module(name: str):
    """Imported the way the platform imports it, isolation included."""
    from app.catalog.loader import import_plugin_module

    return import_plugin_module(PLUGIN_DIR, name)


def _kinds(before: str, after: str) -> list[str]:
    detector = _module("detect")
    return [f.kind for f in detector.detect({"m.py": before}, {"m.py": after})]


def test_extract_method_is_named():
    assert _kinds(BEFORE, EXTRACTED) == ["Extract Method"]


def test_rename_keeps_the_body_and_the_owner():
    after = BEFORE.replace("def helper(self, x):", "def assist(self, x):")
    assert _kinds(BEFORE, after) == ["Rename Method"]


def test_move_keeps_the_name_and_changes_the_owner():
    after = BEFORE.replace(
        "def legacy(a, b):\n    return a * b",
        "class Maths:\n    def legacy(a, b):\n        return a * b")
    assert _kinds(BEFORE, after) == ["Move Method"]


def test_move_and_rename_together():
    after = BEFORE.replace(
        "def legacy(a, b):\n    return a * b",
        "class Maths:\n    def multiply(a, b):\n        return a * b")
    assert _kinds(BEFORE, after) == ["Move & Rename Method"]


def test_inline_removes_the_callee_and_grows_the_caller():
    after = BEFORE.replace(
        "def legacy(a, b):\n    return a * b\n\n\ndef caller():\n    return legacy(2, 3)",
        "def caller():\n    result = 2 * 3\n    return result")
    assert _kinds(BEFORE, after) == ["Inline Method"]


def test_signature_change_is_reported_separately():
    after = BEFORE.replace("def helper(self, x):", "def helper(self, x, y):")
    assert _kinds(BEFORE, after) == ["Change Method Signature"]


def test_reformatting_alone_is_not_a_refactoring():
    after = BEFORE.replace('"""Doc."""', '"""Documentation."""') + "\n# trailing comment\n"
    assert _kinds(BEFORE, after) == []


def test_unparseable_output_is_reported_not_swallowed():
    detector = _module("detect")
    findings = detector.detect({"m.py": BEFORE}, {"m.py": "def broken(:\n    pass\n"})
    assert [f.kind for f in findings] == [detector.SYNTAX_ERROR]
    assert "line 1" in findings[0].detail


def test_expected_kinds_are_matched_case_and_separator_insensitively():
    detector = _module("detect")
    findings = detector.detect({"m.py": BEFORE}, {"m.py": EXTRACTED})
    assert detector.matches(findings, ["extract_method"]) == ["extract_method"]
    assert detector.matches(findings, ["Extract Method"]) == ["Extract Method"]
    assert detector.matches(findings, ["Inline Method"]) == []


# --- the preset, against a real workspace --------------------------------

def _workspace(tmp_path: Path, before: str, after: str) -> tuple[Path, str]:
    workspace = tmp_path / "workspace"
    (workspace / "pkg").mkdir(parents=True)
    target = workspace / "pkg" / "report.py"
    target.write_text(before, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "-A"], cwd=workspace, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "baseline"], cwd=workspace, check=True)
    target.write_text(after, encoding="utf-8")
    diff = subprocess.run(["git", "diff"], cwd=workspace, capture_output=True,
                          text=True, check=True).stdout
    return workspace, diff


def _context(tmp_path: Path, workspace: Path, diff: str, params: dict | None = None):
    from app.catalog.sdk import EvalContext, TaskDef, WorkspaceSpec

    return EvalContext(
        task=TaskDef(task_key="t", title="t", language="python",
                     workspace=WorkspaceSpec(type="snapshot", source="x"),
                     instructions="", params=params or {}),
        workspace=workspace, artifacts_dir=tmp_path / "art", data_root=tmp_path / "data",
        session=None, diff_text=diff, advisory=False,
    )


def test_preset_reads_the_baseline_from_the_commit(tmp_path):
    plugin = _module("plugin")
    workspace, diff = _workspace(tmp_path, BEFORE, EXTRACTED)
    result = pyrefactor().measure(_context(tmp_path, workspace, diff), {})
    assert result.ok is True
    assert result.name == "pyrefactor", "the recorded stage is the plugin's directory name"
    assert result.outputs["detectedCount"] == 1
    assert result.outputs["filesAnalysed"] == 1
    assert "Extract Method" in result.outputs["detected"][0]


def test_preset_reports_an_unreadable_baseline_rather_than_no_refactoring(tmp_path):
    """The defect that scored a correct rename as no refactoring at all.

    Evaluation reads a workspace the agent owns, so a git read can fail for
    reasons that have nothing to do with the change. Reporting it keeps a
    correct refactoring from being recorded as an agent failure.
    """
    plugin = _module("plugin")
    workspace, diff = _workspace(tmp_path, BEFORE, EXTRACTED)
    shutil.rmtree(workspace / ".git")
    result = pyrefactor().measure(_context(tmp_path, workspace, diff), {})
    assert result.ok is False
    assert result.reason == "ast_verification_failed"
    assert "pkg/report.py" in result.message
    assert "before the agent ran" in result.message
    assert "detected nothing" not in result.message


def test_preset_fails_when_the_expected_refactoring_is_absent(tmp_path):
    plugin = _module("plugin")
    workspace, diff = _workspace(tmp_path, BEFORE, EXTRACTED)
    context = _context(tmp_path, workspace, diff, {"refactoring_type": "inline_method"})
    result = pyrefactor().measure(context, {"expected_from": "params.refactoring_type"})
    assert result.ok is False
    assert result.reason == "ast_verification_failed"
    assert "Expected inline_method" in result.message
    assert result.outputs["matched"] == []


def test_preset_passes_when_the_task_names_the_refactoring(tmp_path):
    plugin = _module("plugin")
    workspace, diff = _workspace(tmp_path, BEFORE, EXTRACTED)
    context = _context(tmp_path, workspace, diff, {"refactoring_type": "extract method"})
    result = pyrefactor().measure(context, {"expected_from": "params.refactoring_type"})
    assert result.ok is True
    assert result.outputs["matched"] == ["extract method"]


def test_preset_fails_on_a_broken_file_even_if_something_was_detected(tmp_path):
    plugin = _module("plugin")
    workspace, diff = _workspace(tmp_path, BEFORE, "class Report:\n    def render(self:\n")
    result = pyrefactor().measure(_context(tmp_path, workspace, diff), {})
    assert result.ok is False
    assert "does not parse" in result.message
    assert result.outputs["parseErrors"]


def test_preset_reports_when_no_python_changed(tmp_path):
    plugin = _module("plugin")
    workspace, _ = _workspace(tmp_path, BEFORE, BEFORE)
    result = pyrefactor().measure(_context(tmp_path, workspace, "diff --git a/README.md b/README.md\n"
                                                      "--- a/README.md\n+++ b/README.md\n"), {})
    assert result.ok is False
    assert result.message == "No Python file was changed."


def test_metric_is_reachable_by_the_name_of_its_directory():
    """One plugin, one metric, and the directory name is the id.

    A benchmark's manifest names `pyrefactor`, and so does the evidence a
    finished task records: nothing has to know which plugin provided it.
    """
    from app.catalog.loader import discover
    from app.evaluation import registry

    loaded = discover(PLUGINS)
    assert loaded.errors == []
    assert "pyrefactor" in loaded.evaluation
    assert loaded.evaluation["pyrefactor"].metric_id == "pyrefactor"

    found = registry.get("pyrefactor")
    assert found is not None
    assert found.plugin_dir == PLUGIN_DIR
    assert found.reason == "ast_verification_failed"
    assert found.spec.title and found.spec.summary
    assert registry.get("pyrefactor.detect") is None, "the dotted form is gone"
