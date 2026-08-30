"""The extension points, exercised the way a third party would use them.

Each test here fails if adding something new starts to require editing the
platform: a model provider must be reachable from configuration alone, and a
measurement must be usable from a dropped-in plugin without the core knowing
its name.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from helpers import FIXTURES


# --------------------------------------------------------------------------- #
# providers
# --------------------------------------------------------------------------- #

def _settings(**overrides):
    from app.config import Defaults, ProviderConfig, Settings

    return Settings(
        defaults=Defaults(**overrides.pop("defaults", {})),
        providers=[
            ProviderConfig(
                key="openrouter", name="OpenRouter",
                base_url="https://openrouter.ai/api/v1",
                api_key_env="OPENROUTER_API_KEY", base_url_env="OPENROUTER_BASE_URL",
                credits=True,
            ),
            ProviderConfig(
                key="inhouse", name="In-house gateway",
                base_url="https://llm.example.internal/v1",
                api_key_env="INHOUSE_LLM_KEY", base_url_env="INHOUSE_LLM_BASE_URL",
            ),
        ],
        **overrides,
    )


def test_a_new_provider_is_reachable_from_configuration_alone(monkeypatch):
    """`inhouse` exists nowhere in the platform's code — only in config."""
    monkeypatch.setenv("INHOUSE_LLM_KEY", "secret-value")
    monkeypatch.setenv("RP_PROVIDER", "inhouse")
    settings = _settings()

    assert settings.active_provider().key == "inhouse"
    assert settings.provider_base_url() == "https://llm.example.internal/v1"

    env = settings.provider_agent_env()
    # the adapter reads the neutral pair, so it needs no per-vendor branch
    assert env["RP_PROVIDER_BASE_URL"] == "https://llm.example.internal/v1"
    assert env["RP_PROVIDER_API_KEY"] == "secret-value"
    # and the provider's own variable name is passed through for adapters that
    # already speak it
    assert env["INHOUSE_LLM_KEY"] == "secret-value"
    assert "OPENROUTER_API_KEY" not in env


def test_provider_endpoint_is_overridable_without_touching_config(monkeypatch):
    monkeypatch.setenv("INHOUSE_LLM_BASE_URL", "http://127.0.0.1:8000/v1")
    monkeypatch.setenv("RP_PROVIDER", "inhouse")
    assert _settings().provider_base_url() == "http://127.0.0.1:8000/v1"


def test_unknown_selection_falls_back_instead_of_crashing(monkeypatch):
    monkeypatch.setenv("RP_PROVIDER", "does-not-exist")
    assert _settings().active_provider().key == "openrouter"


def test_agent_env_omits_absent_credentials(monkeypatch):
    """A missing key must stay missing: half-configured access should fail at
    the adapter with a clear message, not send an empty Authorization header."""
    monkeypatch.delenv("INHOUSE_LLM_KEY", raising=False)
    monkeypatch.setenv("RP_PROVIDER", "inhouse")
    assert "RP_PROVIDER_API_KEY" not in _settings().provider_agent_env()


def test_shipped_configuration_declares_more_than_one_provider():
    """Guards the regression this replaced: a single vendor wired into code."""
    import yaml

    raw = yaml.safe_load((Path(__file__).parents[2] / "config.yaml").read_text(encoding="utf-8"))
    keys = {entry["key"] for entry in raw["providers"]}
    assert {"openrouter", "openai", "local"} <= keys
    assert raw["defaults"]["provider"] in keys


def test_a_configured_providers_key_is_redacted_like_a_shipped_one(monkeypatch):
    """Redaction must follow the registry. A key belonging to a provider the
    platform has never heard of is still a key."""
    from app import config as config_mod
    from app.results.redaction import Redactor

    monkeypatch.setenv("ACME_LLM_KEY", "acme-live-9f3c1d77aa21")
    monkeypatch.setattr(config_mod, "get_settings", lambda: _settings_with_acme())

    redacted = Redactor.from_environment().redact_text(
        "curl -H 'Authorization: Bearer acme-live-9f3c1d77aa21' https://llm.acme.test/v1"
    )
    assert "acme-live-9f3c1d77aa21" not in redacted


def _settings_with_acme():
    from app.config import ProviderConfig, Settings

    return Settings(providers=[ProviderConfig(key="acme", api_key_env="ACME_LLM_KEY")])


def test_credential_shaped_assignments_are_redacted_without_naming_a_vendor():
    from app.results.redaction import Redactor

    text = "VENDORX_API_KEY=abcdef123456\nOPENROUTER_API_KEY=sk-or-v1-abcdef123456\n"
    redacted = Redactor().redact_text(text)
    assert "abcdef123456" not in redacted


def test_the_shipped_agent_adapter_names_no_vendor():
    """The Copilot adapter must consume the neutral variables only."""
    source = (Path(__file__).parents[2] / "plugins/agents/copilot/plugin.py").read_text(encoding="utf-8")
    assert "OPENROUTER" not in source
    assert "RP_PROVIDER_BASE_URL" in source and "RP_PROVIDER_API_KEY" in source


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #

def test_a_metric_plugin_provides_one_metric_named_after_its_directory():
    """The naming rule, in one assertion.

    Ids were namespaced `<plugin>.<stage>`, so the same measurement could be
    reached under two spellings and a benchmark manifest named something no
    directory matched. One plugin provides one metric and its directory is its
    id, which makes ids unique by construction.
    """
    from app.catalog.loader import discover
    from app.evaluation import registry

    reg = discover(FIXTURES)
    assert "fixturemetric" in reg.evaluation
    assert reg.evaluation["fixturemetric"].metric_id == "fixturemetric"

    found = registry.get("fixturemetric")
    assert found is not None and found.id == "fixturemetric"
    assert found.plugin_dir.name == "fixturemetric"
    assert registry.get("fixturemetric.diff_budget") is None


def test_a_metric_id_must_read_the_same_everywhere_it_is_recorded():
    """An id appears in evidence, exports and manifests, so it is restricted.

    A directory whose name the manifest contradicts is refused: otherwise the
    metric a benchmark references and the directory an author edits are two
    different names.
    """
    from app.catalog.loader import METRIC_ID

    assert METRIC_ID.fullmatch("java_build")
    assert not METRIC_ID.fullmatch("pytest.suite")
    assert not METRIC_ID.fullmatch("Java_Build")
    assert not METRIC_ID.fullmatch("2fast")


def test_discovery_forgets_metrics_that_are_no_longer_installed(tmp_path):
    from app.catalog.loader import discover
    from app.evaluation import registry

    discover(FIXTURES)
    assert registry.ids()
    discover(tmp_path)          # an installation without the plugin
    assert registry.ids() == []


def _eval_context(tmp_path, diff_text: str):
    from app.catalog.sdk import EvalContext, TaskDef, WorkspaceSpec

    task = TaskDef(
        task_key="t-1", title="t", language="java",
        workspace=WorkspaceSpec(type="snapshot", source="."), instructions="",
    )
    return EvalContext(
        task=task, workspace=tmp_path, artifacts_dir=tmp_path / "artifacts",
        data_root=tmp_path, session=None, diff_text=diff_text, advisory=False,
    )


def _bench(passed: str, config: dict):
    from app.catalog.loader import LoadedBenchmark
    from app.catalog.manifest import BenchmarkManifest
    from app.catalog.sdk import BenchmarkPlugin

    manifest = BenchmarkManifest.model_validate({
        "type": "benchmark", "key": "b", "name": "B", "language": "java",
        "evaluation": {
            "capture": [],
            "verify": [{"preset": "fixturemetric", "config": config}],
            "passed": passed,
        },
    })
    return LoadedBenchmark(manifest=manifest, plugin_dir=Path("."), tasks=[], hooks=BenchmarkPlugin())


@pytest.mark.parametrize(
    "diff_text,budget,expect_pass",
    [("+a\n+b\n", 5, True), ("+a\n+b\n+c\n", 2, False)],
)
def test_a_plugin_metric_can_decide_the_verdict(tmp_path, diff_text, budget, expect_pass):
    from app.catalog.loader import discover
    from app.evaluation import engine

    discover(FIXTURES)
    outcome = engine.evaluate(
        _bench("fixturemetric", {"max_changed_lines": budget}),
        _eval_context(tmp_path, diff_text),
    )
    assert outcome.passed is expect_pass
    assert outcome.details["fixturemetric"]["changedLines"] == len(diff_text.split())
    if not expect_pass:
        # the reason code comes from the plugin, not from a core table
        assert outcome.reason == "diff_too_large"


def test_operator_can_retune_a_plugin_metric_like_any_other(tmp_path):
    """Settings overrides are keyed by metric id, so they must reach a metric
    the platform does not ship."""
    from app.catalog.loader import discover
    from app.evaluation import engine

    discover(FIXTURES)
    loaded = _bench("fixturemetric", {"max_changed_lines": 1})
    override = {"verify": [{"preset": "fixturemetric", "config": {"max_changed_lines": 99}}]}
    outcome = engine.evaluate(loaded, _eval_context(tmp_path, "+a\n+b\n+c\n"), override)
    assert outcome.passed is True


def test_referencing_a_metric_that_is_not_installed_is_an_error(tmp_path):
    from app.catalog.loader import discover
    from app.evaluation import engine

    discover(tmp_path)
    with pytest.raises(KeyError):
        engine.evaluate(_bench("ghost_metric", {}), _eval_context(tmp_path, ""))


def test_a_third_party_metric_describes_itself_like_a_shipped_one():
    """The operator sees what a metric measures and what it accepts.

    Without this the settings page could only offer an id and a free-text JSON
    blob, which means reading the plugin's source to tune it. A third-party
    metric and a shipped one are described in the same shape, so neither is
    privileged.
    """
    from app.catalog.loader import discover
    from app.evaluation import metrics

    discover(FIXTURES)
    described = metrics.catalogue()
    entry = described["fixturemetric"]
    assert entry["title"] == "Change budget"
    assert entry["reason"] == "diff_too_large"
    assert entry["gates"] is True
    assert entry["requires"] == "nothing beyond the captured diff"
    assert entry["outputs"] == ["changedLines", "budget"]
    assert entry["options"] == [{
        "key": "max_changed_lines", "label": "Budget", "type": "integer",
        "default": 50, "help": "", "unit": "lines", "choices": [],
    }]
    assert described["workspace_changed"]["title"] == "Workspace changed"
    assert set(described["fixturemetric"]) == set(described["workspace_changed"])


def test_every_shipped_metric_describes_itself():
    """A metric with no statement of what it measures is unreadable in the UI."""
    from app.catalog.loader import discover
    from app.evaluation import metrics

    discover(Path(__file__).parents[2] / "plugins")
    for metric_id, entry in metrics.catalogue().items():
        assert entry["title"], f"{metric_id} declares no title"
        assert entry["summary"], f"{metric_id} does not say what it measures"
        assert entry["requires"], f"{metric_id} does not say what it needs"
        if entry["gates"]:
            assert entry["reason"], f"{metric_id} can fail a task and declares no reason code"


def _benchmark_manifests():
    import yaml

    from app.catalog.manifest import BenchmarkManifest

    for path in sorted((Path(__file__).parents[2] / "plugins" / "benchmarks").glob("*/plugin.yaml")):
        yield path.parent, BenchmarkManifest(**yaml.safe_load(path.read_text(encoding="utf-8")))


def test_a_benchmark_declares_what_fills_its_prompt_without_writing_python():
    """A prompt template was a file name and a text box.

    Which values the benchmark substitutes decides whether an edit is still
    usable, so a benchmark that ships no plugin code has to be able to name them
    in its manifest; the platform's generic description remains for one that
    does not.
    """
    from app.api.prompts import _spec

    class Loaded:
        def __init__(self, manifest):
            self.manifest, self.hooks = manifest, None

    manifests = {manifest.key: (directory, manifest) for directory, manifest in _benchmark_manifests()}
    _, declared = manifests["pyrefactor-live"]
    spec = _spec(Loaded(declared), {}, "task.md")
    assert spec.syntax == "jinja"
    assert spec.applies_to == "every task in this benchmark"
    assert [(v.name, v.required) for v in spec.variables] == [
        ("task.instructions", True), ("params.refactoring", True),
        ("params.module", True), ("params.tests", False),
    ]
    assert all(v.summary for v in spec.variables)

    silent = declared.model_copy(update={"prompt": declared.prompt.model_copy(update={"variables": []})})
    fallback = _spec(Loaded(silent), {}, "task.md")
    assert [v.name for v in fallback.variables] == ["task.instructions", "params"]


def test_every_shipped_prompt_template_is_described_and_holds_its_own_values():
    """A declaration that the shipped template contradicts would block its own
    benchmark: the editor refuses to save a template missing a required value."""
    from app.api.prompts import _declared, _present, _spec

    class Loaded:
        def __init__(self, directory, manifest):
            self.manifest, self.plugin_dir = manifest, directory
            self.hooks = None

    for directory, manifest in _benchmark_manifests():
        hooks = None
        if manifest.entrypoint:                     # a plugin may describe per template
            from app.catalog.loader import import_plugin_module

            module_name, _, attribute = manifest.entrypoint.partition(":")
            hooks = getattr(import_plugin_module(directory, module_name), attribute)()
        loaded = Loaded(directory, manifest)
        loaded.hooks = hooks
        declared = _declared(loaded)
        for template in sorted((directory / "prompts").glob("*")):
            spec = _spec(loaded, declared, template.name)
            assert spec.syntax, f"{manifest.key}/{template.name} describes no syntax"
            assert spec.variables, f"{manifest.key}/{template.name} names no substituted value"
            content = template.read_text(encoding="utf-8")
            missing = [v.name for v in spec.variables
                       if v.required and not _present(content, spec.syntax, v.name)]
            assert not missing, f"{manifest.key}/{template.name} is missing {missing}"


def test_a_metric_the_deployment_no_longer_ships_is_named_rather_than_hidden(tmp_path):
    """A manifest can outlive an uninstalled metric. The run fails loudly on it;
    the settings page has to say which one instead of showing an empty row."""
    from app.catalog.loader import discover
    from app.evaluation import metrics

    discover(tmp_path)
    entry = metrics.describe("ghost_metric", metrics.catalogue())
    assert entry["title"] == "ghost_metric"
    assert entry["available"] is False
    assert "plugins/evaluation/" in entry["unavailable"]


def test_a_benchmark_references_metrics_and_cannot_define_one(tmp_path):
    """The rule that gives every measurement one home.

    A metric defined inside a benchmark could not be referenced by another
    benchmark, retuned from Settings, or found by anyone who did not know that
    benchmark's source. Loading such a benchmark fails, naming it and where the
    measurement belongs.
    """
    from app.catalog.loader import discover

    benchmark = tmp_path / "benchmarks" / "greedy"
    benchmark.mkdir(parents=True)
    (benchmark / "plugin.yaml").write_text(
        "type: benchmark\nkey: greedy\nname: Greedy\nlanguage: java\n"
        "entrypoint: plugin:Plugin\n"
        "evaluation:\n  capture: [git_diff]\n  verify: [workspace_changed]\n"
        "  passed: workspace_changed\n", encoding="utf-8")
    (benchmark / "plugin.py").write_text(
        "from app.catalog.sdk import BenchmarkPlugin, StageResult\n"
        "class Plugin(BenchmarkPlugin):\n"
        "    def stages(self):\n"
        "        return {'greedy.mine': lambda ctx, config: StageResult(ok=True)}\n",
        encoding="utf-8")

    reg = discover(tmp_path)
    assert "greedy" not in reg.benchmarks
    assert any("greedy" in error and "plugins/evaluation/" in error for error in reg.errors), reg.errors


def test_a_benchmark_may_prepare_the_workspace_and_must_describe_that_step():
    """Preparation is not a measurement, and is not disguised as one.

    The Java benchmark stages what its metrics compare. That step decides no
    verdict, so it is declared as preparation, described where it is implemented,
    and shown as the pipeline's first step.
    """
    from app.catalog.loader import discover
    from app.evaluation import metrics, registry

    reg = discover(Path(__file__).parents[2] / "plugins")
    swe = reg.benchmarks["swe"]

    assert swe.manifest.evaluation.prepare == "prepare_candidate"
    assert registry.get("prepare_candidate") is None, "preparation is not a metric"
    assert "swe.codebleu" not in registry.ids() and "codebleu" in registry.ids()

    spec = swe.hooks.describe_preparation()
    assert spec is not None and spec.title and spec.summary
    entry = metrics.preparation(swe.manifest.evaluation.prepare, spec)
    assert entry["gates"] is False and entry["options"] == []


def test_a_declared_preparation_step_must_be_implemented(tmp_path):
    """A manifest that names a step no code implements would run nothing."""
    from app.catalog.loader import discover

    benchmark = tmp_path / "benchmarks" / "absent"
    benchmark.mkdir(parents=True)
    (benchmark / "plugin.yaml").write_text(
        "type: benchmark\nkey: absent\nname: Absent\nlanguage: java\n"
        "evaluation:\n  prepare: stage_it\n  verify: [workspace_changed]\n"
        "  passed: workspace_changed\n", encoding="utf-8")

    reg = discover(tmp_path)
    assert "absent" not in reg.benchmarks
    assert any("prepare" in error for error in reg.errors), reg.errors


# --------------------------------------------------------------------------- #
# isolation between installed plugins
# --------------------------------------------------------------------------- #

def _agent_with_own_events_module(root: Path, key: str, marker: str, style: str) -> None:
    """An adapter that keeps its parser in `events.py`, as all three shipped
    adapters do. A plugin author cannot know which module names the other
    installed plugins already use, so the name must not have to be unique.

    `style` is how the adapter reaches its own module: relative to itself, or
    by bare name after putting its directory on the import path.
    """
    imports = {
        "relative": "from . import events as events_mod\n",
        "bare": ("import sys\n"
                 "from pathlib import Path as _P\n"
                 "sys.path.insert(0, str(_P(__file__).parent))\n"
                 "import events as events_mod\n"),
    }[style]
    plugin_dir = root / "agents" / key
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text(
        f"type: agent\nkey: {key}\nname: {key}\nversion: 1.0.0\n"
        f"entrypoint: plugin:Plugin\n", encoding="utf-8")
    (plugin_dir / "events.py").write_text(f'MARKER = "{marker}"\n', encoding="utf-8")
    (plugin_dir / "plugin.py").write_text(
        "from __future__ import annotations\n"
        "from app.catalog.sdk import AgentPlugin, CommandSpec, SessionInfo\n"
        + imports +
        "class Plugin(AgentPlugin):\n"
        "    def prepare(self, session):\n"
        "        session.config_dir.mkdir(parents=True, exist_ok=True)\n"
        "    def command(self, session):\n"
        "        return CommandSpec(argv=['true'], env={}, cwd=session.workspace)\n"
        "    def events_path(self, session):\n"
        "        return session.config_dir / 'events.jsonl'\n"
        "    def parse_session(self, events_path, terminal_log_path):\n"
        "        return SessionInfo(model=events_mod.MARKER)\n",
        encoding="utf-8")


@pytest.mark.parametrize("style", ["relative", "bare"])
def test_two_plugins_may_ship_a_module_of_the_same_name(tmp_path, style):
    """Each plugin's own modules are private to it.

    Sharing one module namespace meant the first plugin loaded answered for
    every later one: three installed adapters each shipping `events.py` all ran
    the first adapter's parser, and the run died on the resulting mismatch.
    A third-party plugin that reaches its module by bare name is isolated by
    the loader rather than trusted to pick a name nobody else took.
    """
    from app.catalog.loader import discover

    _agent_with_own_events_module(tmp_path, "alpha", "alpha-marker", style)
    _agent_with_own_events_module(tmp_path, "beta", "beta-marker", style)

    reg = discover(tmp_path)
    assert not reg.errors, reg.errors
    parsed = {key: agent.impl.parse_session(None, tmp_path / "terminal.log").model
              for key, agent in reg.agents.items()}
    assert parsed == {"alpha": "alpha-marker", "beta": "beta-marker"}


def test_two_benchmarks_may_ship_a_provisioning_helper_of_the_same_name(tmp_path):
    """Provisioning is subject to the same isolation as the rest of a plugin.

    It runs in a thread per benchmark at start-up, so a shared module namespace
    would let one benchmark provision its data with another's helper.
    """
    from app.catalog.bootstrap import _bootstrap_fn
    from app.catalog.loader import discover

    for key, marker in (("alpha", "alpha-data"), ("beta", "beta-data")):
        plugin_dir = tmp_path / "benchmarks" / key
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text(
            f"type: benchmark\nkey: {key}\nname: {key}\nversion: 1.0.0\nlanguage: python\n"
            f"setups: [s1]\ndata:\n  bootstrap: data_bootstrap.py\n"
            f"prompt:\n  template: p.md\nevaluation:\n"
            f"  verify:\n    - {{preset: workspace_changed}}\n  passed: workspace_changed\n",
            encoding="utf-8")
        (plugin_dir / "tasks.yaml").write_text(
            f"tasks:\n  - task_key: {key}/t\n    title: t\n    instructions: do\n"
            f"    workspace: {{type: snapshot, source: x}}\n", encoding="utf-8")
        (plugin_dir / "p.md").write_text("{{ task.instructions }}", encoding="utf-8")
        (plugin_dir / "helper.py").write_text(f'MARKER = "{marker}"\n', encoding="utf-8")
        (plugin_dir / "data_bootstrap.py").write_text(
            "from pathlib import Path\n"
            "from . import helper\n"
            "def bootstrap(data_dir: Path) -> None:\n"
            "    data_dir.mkdir(parents=True, exist_ok=True)\n"
            "    (data_dir / 'provisioned.txt').write_text(helper.MARKER, encoding='utf-8')\n",
            encoding="utf-8")

    reg = discover(tmp_path)
    assert not reg.errors, reg.errors
    for key, expected in (("alpha", "alpha-data"), ("beta", "beta-data")):
        loaded = reg.benchmarks[key]
        _bootstrap_fn(loaded)(loaded.data_dir)
        assert (loaded.data_dir / "provisioned.txt").read_text(encoding="utf-8") == expected


def test_every_shipped_adapter_parses_a_session_into_the_contract_type(tmp_path):
    """Discovery of the real installation, then each adapter reads a session.

    Loading one adapter at a time hides a collision between them, which is why
    this discovers the shipped set together and exercises all of them.
    """
    from app.catalog.loader import discover
    from app.catalog.sdk import SessionInfo

    terminal_log = tmp_path / "terminal.log"
    terminal_log.write_text("", encoding="utf-8")

    reg = discover(Path(__file__).parents[2] / "plugins")
    assert {"aider", "codex", "copilot"} <= set(reg.agents)
    for key, agent in reg.agents.items():
        info = agent.impl.parse_session(None, terminal_log)
        assert isinstance(info, SessionInfo), f"{key} returned {type(info).__name__}"
