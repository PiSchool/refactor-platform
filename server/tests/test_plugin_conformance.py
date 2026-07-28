"""Every plugin the repository ships, and every example it offers, conforms.

`make plugins` runs the same checks over the shipped plugins, and
`make plugin PLUGIN=<dir>` runs them over one a contributor is writing. This
module is that check as a test, so a change to a contract cannot pass CI while
leaving a shipped plugin behind it.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from app.catalog.verify import plugin_dirs, verify_plugin

REPO = Path(__file__).resolve().parents[2]
SHIPPED = REPO / "plugins"
EXAMPLES = REPO / "examples" / "plugins"


def _fatal(problems) -> list[str]:
    return [str(problem) for problem in problems if problem.fatal]


@pytest.mark.parametrize("plugin", sorted(plugin_dirs(SHIPPED)), ids=lambda p: p.name)
def test_every_shipped_plugin_conforms(plugin: Path) -> None:
    assert _fatal(verify_plugin(plugin, shipped=SHIPPED)) == []


@pytest.mark.parametrize("plugin", sorted(plugin_dirs(EXAMPLES)), ids=lambda p: p.name)
def test_every_example_plugin_conforms(plugin: Path) -> None:
    """An example is what a contributor copies, so it carries no warning either."""
    problems = verify_plugin(plugin, shipped=SHIPPED)
    assert [str(problem) for problem in problems] == []


def test_one_example_exists_per_extension_point() -> None:
    kinds = {path.parent.name for path in plugin_dirs(EXAMPLES)}
    assert kinds == {"benchmarks", "agents", "evaluation", "lsp"}


def test_a_key_that_disagrees_with_its_directory_is_reported(tmp_path: Path) -> None:
    plugin = tmp_path / "plugins" / "evaluation" / "mine"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text(
        "type: evaluation\nkey: something_else\nentrypoint: plugin:Plugin\n", encoding="utf-8"
    )
    problems = _fatal(verify_plugin(plugin, shipped=SHIPPED))
    assert any("differs from the directory name" in problem for problem in problems), problems


def test_a_manifest_in_the_wrong_place_is_reported(tmp_path: Path) -> None:
    plugin = tmp_path / "plugins" / "agents" / "mine"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text("type: benchmark\nkey: mine\n", encoding="utf-8")
    problems = _fatal(verify_plugin(plugin, shipped=SHIPPED))
    assert any("sits under agents/" in problem for problem in problems), problems


def test_a_benchmark_referencing_an_unknown_metric_is_reported(tmp_path: Path) -> None:
    """The failure a contributor would otherwise meet on the first scored task."""
    plugin = tmp_path / "plugins" / "benchmarks" / "mine"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text(textwrap.dedent("""
        type: benchmark
        key: mine
        name: Mine
        language: python
        evaluation:
          capture: [git_diff]
          verify:
            - {preset: no_such_metric}
          passed: "no_such_metric"
    """), encoding="utf-8")
    (plugin / "tasks.yaml").write_text(textwrap.dedent("""
        tasks:
          - task_key: t1
            title: One task
            workspace: {type: snapshot, source: repo}
            instructions: Do the thing.
    """), encoding="utf-8")
    problems = _fatal(verify_plugin(plugin, shipped=SHIPPED))
    assert any("no_such_metric" in problem for problem in problems), problems


def test_an_agent_that_breaks_the_session_contract_is_reported(tmp_path: Path) -> None:
    """The defect this check exists for: the failure lands after the model has
    already run, on every task, and names no plugin."""
    plugin = tmp_path / "plugins" / "agents" / "mine"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text(
        "type: agent\nkey: mine\nname: Mine\nbinary: bash\nentrypoint: plugin:Plugin\n",
        encoding="utf-8",
    )
    (plugin / "plugin.py").write_text(textwrap.dedent('''
        from pathlib import Path

        from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx


        class Plugin(AgentPlugin):
            def prepare(self, session: SessionCtx) -> None: ...

            def command(self, session: SessionCtx) -> CommandSpec:
                return CommandSpec(argv=["true"], env={}, cwd=session.workspace)

            def events_path(self, session: SessionCtx):
                return None

            def parse_session(self, events_path, terminal_log_path: Path):
                return {"model": "mine"}
    '''), encoding="utf-8")
    problems = _fatal(verify_plugin(plugin, shipped=SHIPPED))
    assert any("SessionInfo" in problem for problem in problems), problems
