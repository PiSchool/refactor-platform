"""Plugin discovery: scan plugins/{benchmarks,agents,evaluation,lsp}, validate
manifests, import optional Python modules, load task files."""
from __future__ import annotations

import importlib.util
import re
import shutil
import sys
import threading
import types
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.catalog.manifest import (
    AgentManifest,
    BenchmarkManifest,
    EvaluationManifest,
    LspManifest,
    TaskEntry,
    TasksFile,
)
from app.catalog.sdk import (
    AgentPlugin,
    BenchmarkPlugin,
    EvaluationPlugin,
    LSPPlugin,
    TaskDef,
    WorkspaceSpec,
)
from app.evaluation import registry as eval_registry


@dataclass
class LoadedBenchmark:
    manifest: BenchmarkManifest
    plugin_dir: Path
    tasks: list[TaskDef]
    hooks: BenchmarkPlugin

    @property
    def data_dir(self) -> Path:
        return self.plugin_dir / "data"


@dataclass
class LoadedAgent:
    manifest: AgentManifest
    plugin_dir: Path
    impl: AgentPlugin

    @property
    def binary_path(self) -> str | None:
        """Resolved path of the adapter's CLI, or None when it is not on PATH.

        Looked up on each access: installing the tool takes effect without a
        restart.
        """
        if not self.manifest.binary:
            return None
        return shutil.which(self.manifest.binary)

    @property
    def available(self) -> bool:
        return not self.manifest.binary or self.binary_path is not None

    def unavailable_reason(self) -> str:
        if self.available:
            return ""
        hint = f" Install it with: {self.manifest.install}" if self.manifest.install else ""
        return (f"agent {self.manifest.key!r} needs {self.manifest.binary!r} on PATH "
                f"and it was not found.{hint}")


@dataclass
class LoadedEvaluation:
    manifest: EvaluationManifest
    plugin_dir: Path
    impl: EvaluationPlugin

    @property
    def metric_id(self) -> str:
        """The id benchmarks reference, which is the plugin's directory name."""
        return self.manifest.key


@dataclass
class LoadedLsp:
    manifest: LspManifest
    plugin_dir: Path
    impl: LSPPlugin


@dataclass
class Registry:
    benchmarks: dict[str, LoadedBenchmark] = field(default_factory=dict)
    agents: dict[str, LoadedAgent] = field(default_factory=dict)
    evaluation: dict[str, LoadedEvaluation] = field(default_factory=dict)
    lsp: dict[str, LoadedLsp] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def lsp_for(self, language: str) -> LoadedLsp | None:
        for loaded in self.lsp.values():
            if loaded.manifest.language == language:
                return loaded
        return None


def _package_name(plugin_dir: Path) -> str:
    raw = f"rp_plugin_{plugin_dir.parent.name}_{plugin_dir.name}"
    return "".join(c if c.isalnum() or c == "_" else "_" for c in raw)


def _plugin_package(plugin_dir: Path) -> str:
    """Register a package whose search path is this plugin's directory.

    A plugin's own modules are its submodules, so two plugins that both ship a
    module of the same name keep their own. Without this, three agent adapters
    that each ship `events.py` share one `sys.modules["events"]`: the first one
    loaded answers for all of them, and the others run someone else's parser.
    """
    name = _package_name(plugin_dir)
    package = sys.modules.get(name)
    if package is None:
        package = types.ModuleType(name)
        package.__path__ = [str(plugin_dir)]
        package.__package__ = name
        sys.modules[name] = package
    return name


# `sys.path` and `sys.modules` are process-wide, and benchmark provisioning
# imports plugins from a thread per benchmark. Reentrant because a plugin's
# import may import another module of the same plugin.
_import_guard = threading.RLock()


@contextmanager
def _plugin_imports(plugin_dir: Path, package: str):
    """Import context for one plugin: its directory is importable, and the
    modules it imports from there stay private to it.

    A plugin that imports a sibling by bare name (`import events`) is isolated
    here rather than trusted to namespace itself, because a third-party plugin
    cannot know what names other installed plugins already occupy.
    """
    with _import_guard:
        original_path = list(sys.path)
        before = set(sys.modules)
        sys.path.insert(0, str(plugin_dir))
        try:
            yield
        finally:
            sys.path[:] = original_path
            for name in set(sys.modules) - before:
                if "." in name or name == package:
                    continue
                module = sys.modules[name]
                origin = getattr(module, "__file__", None)
                if origin and Path(origin).resolve().is_relative_to(plugin_dir.resolve()):
                    sys.modules.setdefault(f"{package}.{name}", module)
                    del sys.modules[name]


def import_plugin_module(plugin_dir: Path, module_name: str):
    """Import one module of a plugin, isolated from every other plugin.

    The only supported way to import plugin code. Importing a plugin's file
    directly bypasses the isolation, which is how a collision between two
    installed plugins stayed invisible to their unit tests.
    """
    file_path = plugin_dir / f"{module_name}.py"
    package = _plugin_package(plugin_dir)
    qualified = f"{package}.{module_name}"
    spec = importlib.util.spec_from_file_location(qualified, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {file_path}")
    module = importlib.util.module_from_spec(spec)
    module.__package__ = package
    sys.modules[qualified] = module
    try:
        with _plugin_imports(plugin_dir, package):
            spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(qualified, None)
        raise
    return module


def _import_entrypoint(plugin_dir: Path, entrypoint: str):
    module_name, _, class_name = entrypoint.partition(":")
    module = import_plugin_module(plugin_dir, module_name)
    cls = getattr(module, class_name or "Plugin")
    return cls()


def _resolve_task(entry: TaskEntry, plugin_dir: Path, default_language: str) -> TaskDef:
    instructions = entry.instructions
    if entry.instructions_file:
        instructions = (plugin_dir / entry.instructions_file).read_text(encoding="utf-8")
    ws = entry.workspace
    return TaskDef(
        task_key=entry.task_key,
        title=entry.title,
        language=entry.language or default_language,
        workspace=WorkspaceSpec(type=ws["type"], source=ws["source"], ref=ws.get("ref")),
        instructions=instructions,
        params=entry.params,
    )


def _load_benchmark(plugin_dir: Path, raw: dict) -> LoadedBenchmark:
    manifest = BenchmarkManifest.model_validate(raw)
    hooks: BenchmarkPlugin = BenchmarkPlugin()
    if manifest.entrypoint:
        hooks = _import_entrypoint(plugin_dir, manifest.entrypoint)
        if not isinstance(hooks, BenchmarkPlugin):
            raise TypeError(f"{manifest.key}: entrypoint is not a BenchmarkPlugin")
    _check_benchmark_contract(manifest, hooks)
    hooks.key = manifest.key
    tasks: list[TaskDef] = []
    tasks_path = plugin_dir / "tasks.yaml"
    if tasks_path.is_file():
        parsed = TasksFile.model_validate(yaml.safe_load(tasks_path.read_text(encoding="utf-8")) or {})
        tasks = [_resolve_task(e, plugin_dir, manifest.language) for e in parsed.tasks]
    return LoadedBenchmark(manifest=manifest, plugin_dir=plugin_dir, tasks=tasks, hooks=hooks)


def _check_benchmark_contract(manifest: BenchmarkManifest, hooks: BenchmarkPlugin) -> None:
    """A benchmark references metrics; it does not define them, and its
    preparation step is declared where it is implemented.

    Both were possible before, and both cost an operator the ability to read a
    pipeline: a measurement defined inside one benchmark cannot be referenced by
    another, retuned from Settings, or found by anyone who does not know that
    benchmark's source.
    """
    for defined in ("stages", "presets"):
        if hasattr(hooks, defined):
            raise TypeError(
                f"{manifest.key}: benchmarks reference metrics by id and do not define "
                f"them ({defined}()); move the measurement to plugins/evaluation/<id>/"
            )
    declares = bool(manifest.evaluation.prepare)
    implements = type(hooks).prepare is not BenchmarkPlugin.prepare
    if declares and not implements:
        raise ValueError(
            f"{manifest.key}: evaluation.prepare names {manifest.evaluation.prepare!r} "
            f"and the plugin implements no prepare()"
        )
    if implements and not declares:
        raise ValueError(
            f"{manifest.key}: the plugin implements prepare() and the manifest does not "
            f"declare evaluation.prepare, so the step would run unnamed"
        )
    if declares and hooks.describe_preparation() is None:
        raise ValueError(
            f"{manifest.key}: prepare() is declared and describe_preparation() returns "
            f"nothing, so the pipeline cannot say what the step does"
        )


def _load_agent(plugin_dir: Path, raw: dict) -> LoadedAgent:
    manifest = AgentManifest.model_validate(raw)
    impl = _import_entrypoint(plugin_dir, manifest.entrypoint)
    if not isinstance(impl, AgentPlugin):
        raise TypeError(f"{manifest.key}: entrypoint is not an AgentPlugin")
    impl.key = manifest.key
    if manifest.capabilities:
        impl.capabilities = {**impl.capabilities, **manifest.capabilities}
    return LoadedAgent(manifest=manifest, plugin_dir=plugin_dir, impl=impl)


#: A metric id appears in stored evidence, in exports and in a manifest, so it is
#: restricted to what reads the same everywhere.
METRIC_ID = re.compile(r"[a-z][a-z0-9_]*\Z")


def _load_evaluation(plugin_dir: Path, raw: dict) -> LoadedEvaluation:
    manifest = EvaluationManifest.model_validate(raw)
    # One metric per plugin, its id the directory name. Ids are then unique by
    # construction and a manifest reference names a directory an author can open.
    if manifest.key != plugin_dir.name:
        raise ValueError(
            f"key {manifest.key!r} differs from the directory name {plugin_dir.name!r}; "
            f"a metric's id is its directory"
        )
    if not METRIC_ID.fullmatch(manifest.key):
        raise ValueError(f"metric id {manifest.key!r} must be {eval_registry.ID_RULE}")
    impl = _import_entrypoint(plugin_dir, manifest.entrypoint)
    if not isinstance(impl, EvaluationPlugin):
        raise TypeError(f"{manifest.key}: entrypoint is not an EvaluationPlugin")
    if not (impl.spec.title and impl.spec.summary):
        raise ValueError(
            f"{manifest.key}: spec must state a title and what the metric measures, "
            f"or the dashboard can only show its id"
        )
    impl.key = manifest.key
    return LoadedEvaluation(manifest=manifest, plugin_dir=plugin_dir, impl=impl)


def _load_lsp(plugin_dir: Path, raw: dict) -> LoadedLsp:
    manifest = LspManifest.model_validate(raw)
    impl = _import_entrypoint(plugin_dir, manifest.entrypoint)
    if not isinstance(impl, LSPPlugin):
        raise TypeError(f"{manifest.key}: entrypoint is not an LSPPlugin")
    impl.key = manifest.key
    impl.language = manifest.language
    return LoadedLsp(manifest=manifest, plugin_dir=plugin_dir, impl=impl)


def discover(plugins_dir: Path) -> Registry:
    registry = Registry()
    loaders = {
        "benchmarks": (_load_benchmark, "benchmarks"),
        "agents": (_load_agent, "agents"),
        "evaluation": (_load_evaluation, "evaluation"),
        "lsp": (_load_lsp, "lsp"),
    }
    # Rebuilt from scratch: a metric plugin that was removed, renamed or failed
    # to load must not stay referenceable from a stale registration.
    eval_registry.reset()
    for kind, (load, attr) in loaders.items():
        base = plugins_dir / kind
        if not base.is_dir():
            continue
        for plugin_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            manifest_path = plugin_dir / "plugin.yaml"
            if not manifest_path.is_file():
                continue
            try:
                raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
                loaded = load(plugin_dir, raw)
                getattr(registry, attr)[loaded.manifest.key] = loaded
                if kind == "evaluation":
                    eval_registry.register(eval_registry.Metric(
                        id=loaded.metric_id, impl=loaded.impl, plugin_dir=plugin_dir))
            except Exception as exc:  # invalid plugin must never break the platform
                registry.errors.append(f"{plugin_dir.name}: {exc}")
    return registry
