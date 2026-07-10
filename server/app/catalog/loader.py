"""Plugin discovery: scan plugins/{benchmarks,agents,lsp}, validate manifests,
import optional Python modules, load task files."""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.catalog.manifest import (
    AgentManifest,
    BenchmarkManifest,
    LspManifest,
    TaskEntry,
    TasksFile,
)
from app.catalog.sdk import AgentPlugin, BenchmarkPlugin, LSPPlugin, TaskDef, WorkspaceSpec


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


@dataclass
class LoadedLsp:
    manifest: LspManifest
    plugin_dir: Path
    impl: LSPPlugin


@dataclass
class Registry:
    benchmarks: dict[str, LoadedBenchmark] = field(default_factory=dict)
    agents: dict[str, LoadedAgent] = field(default_factory=dict)
    lsp: dict[str, LoadedLsp] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def lsp_for(self, language: str) -> LoadedLsp | None:
        for loaded in self.lsp.values():
            if loaded.manifest.language == language:
                return loaded
        return None


def _import_entrypoint(plugin_dir: Path, entrypoint: str):
    module_name, _, class_name = entrypoint.partition(":")
    file_path = plugin_dir / f"{module_name}.py"
    unique = f"rp_plugin_{plugin_dir.parent.name}_{plugin_dir.name}_{module_name}"
    spec = importlib.util.spec_from_file_location(unique, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique] = module
    spec.loader.exec_module(module)
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
    hooks.key = manifest.key
    tasks: list[TaskDef] = []
    tasks_path = plugin_dir / "tasks.yaml"
    if tasks_path.is_file():
        parsed = TasksFile.model_validate(yaml.safe_load(tasks_path.read_text(encoding="utf-8")) or {})
        tasks = [_resolve_task(e, plugin_dir, manifest.language) for e in parsed.tasks]
    return LoadedBenchmark(manifest=manifest, plugin_dir=plugin_dir, tasks=tasks, hooks=hooks)


def _load_agent(plugin_dir: Path, raw: dict) -> LoadedAgent:
    manifest = AgentManifest.model_validate(raw)
    impl = _import_entrypoint(plugin_dir, manifest.entrypoint)
    if not isinstance(impl, AgentPlugin):
        raise TypeError(f"{manifest.key}: entrypoint is not an AgentPlugin")
    impl.key = manifest.key
    if manifest.capabilities:
        impl.capabilities = {**impl.capabilities, **manifest.capabilities}
    if manifest.models:
        impl.models = manifest.models
    return LoadedAgent(manifest=manifest, plugin_dir=plugin_dir, impl=impl)


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
    loaders = {"benchmarks": _load_benchmark, "agents": _load_agent, "lsp": _load_lsp}
    for kind, load in loaders.items():
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
                key = loaded.manifest.key
                target = getattr(registry, kind if kind != "benchmarks" else "benchmarks")
                if kind == "agents":
                    registry.agents[key] = loaded
                elif kind == "lsp":
                    registry.lsp[key] = loaded
                else:
                    registry.benchmarks[key] = loaded
            except Exception as exc:  # invalid plugin must never break the platform
                registry.errors.append(f"{plugin_dir.name}: {exc}")
    return registry
