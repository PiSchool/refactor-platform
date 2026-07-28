"""Check one plugin directory against the contracts before trusting it.

`discover()` is deliberately forgiving: a plugin that raises is collected into
`Registry.errors` so one bad directory cannot take the platform down. That is
correct at runtime and useless to whoever wrote the plugin, who gets one line
naming an exception. This module makes the same expectations explicit, reports
every violation at once, and says what was expected.

The candidate is loaded through the platform's own loader, in the isolated
per-plugin namespace, so a plugin that passes here loads at startup.

    python -m app.catalog.verify plugins/benchmarks/mybench
"""
from __future__ import annotations

import argparse
import inspect
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from app.catalog import loader as catalog_loader
from app.catalog.sdk import EvaluationPlugin, SessionInfo
from app.evaluation import registry as eval_registry

#: directory under `plugins/` -> the `type` its manifests declare
KINDS = {
    "benchmarks": "benchmark",
    "agents": "agent",
    "evaluation": "evaluation",
    "lsp": "lsp",
}

KEY = re.compile(r"[a-z][a-z0-9_-]*\Z")
CAPABILITIES = ("lsp", "subagents", "eval_tool", "retrieval")
WIRES = ("chat_completions", "responses", "anthropic_messages")


@dataclass(frozen=True)
class Problem:
    """One violation. `fatal` distinguishes "will not load" from "will mislead"."""

    message: str
    fatal: bool = True

    def __str__(self) -> str:
        return ("error: " if self.fatal else "warning: ") + self.message


def verify_plugin(path: Path, *, shipped: Path | None = None) -> list[Problem]:
    """Every contract violation in the plugin at `path`.

    `shipped` is the platform's own plugins directory. It is discovered first so
    that a candidate benchmark may reference metrics it does not ship itself.
    """
    path = path.resolve()
    problems: list[Problem] = []
    if not path.is_dir():
        return [Problem(f"{path} is not a directory")]

    kind_dir = path.parent.name
    kind = KINDS.get(kind_dir)
    if kind is None:
        return [Problem(
            f"{path} sits under {kind_dir!r}; a plugin lives in one of "
            f"{', '.join(sorted(KINDS))}, which is how its kind is known"
        )]

    manifest_path = path / "plugin.yaml"
    if not manifest_path.is_file():
        return [Problem(f"{manifest_path} is missing")]
    try:
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return [Problem(f"plugin.yaml does not parse: {exc}")]
    if not isinstance(raw, dict):
        return [Problem("plugin.yaml must be a mapping")]

    declared = raw.get("type")
    if declared != kind:
        problems.append(Problem(
            f"plugin.yaml declares type {declared!r} but sits under {kind_dir}/, "
            f"where the platform looks for {kind!r}"
        ))
    key = str(raw.get("key") or "")
    if not KEY.fullmatch(key):
        problems.append(Problem(
            f"key {key!r} must match {KEY.pattern}: it appears in stored evidence, "
            f"exports and URLs"
        ))
    elif key != path.name:
        problems.append(Problem(
            f"key {key!r} differs from the directory name {path.name!r}; one plugin "
            f"has one name"
        ))
    if problems and any(p.fatal for p in problems):
        # Loading with a broken manifest only repeats what is already reported.
        return problems

    loaded, load_problems = _load(path, kind, shipped)
    problems.extend(load_problems)
    if loaded is None:
        return problems

    checks = {
        "benchmark": _check_benchmark,
        "agent": _check_agent,
        "evaluation": _check_evaluation,
        "lsp": _check_lsp,
    }
    problems.extend(checks[kind](loaded, path))
    return problems


def _load(path: Path, kind: str, shipped: Path | None):
    """Load the candidate through the real loader, in its own namespace.

    The shipped plugins are loaded alongside it in one pass, because `discover()`
    resets the metric registry: a candidate benchmark referencing `java_build`
    can only be checked against a registry that also holds the shipped metrics.
    A candidate whose directory name matches a shipped one replaces it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "plugins"
        for kind_dir in KINDS:
            (root / kind_dir).mkdir(parents=True)
        if shipped and shipped.is_dir():
            for other in plugin_dirs(shipped):
                if other.resolve() != path:
                    (root / other.parent.name / other.name).symlink_to(
                        other.resolve(), target_is_directory=True)
        kind_dir = next(name for name, value in KINDS.items() if value == kind)
        link = root / kind_dir / path.name
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(path, target_is_directory=True)
        registry = catalog_loader.discover(root)

    own = [error for error in registry.errors if error.startswith(f"{path.name}:")]
    if own:
        return None, [Problem(f"the platform cannot load it: {own[0]}")]
    holder = getattr(registry, {"benchmark": "benchmarks", "agent": "agents",
                                "evaluation": "evaluation", "lsp": "lsp"}[kind])
    loaded = next((value for value in holder.values() if value.plugin_dir.name == path.name), None)
    if loaded is None:
        return None, [Problem("the loader accepted the directory but registered nothing")]
    return loaded, []


def _check_benchmark(loaded, path: Path) -> list[Problem]:
    problems: list[Problem] = []
    manifest = loaded.manifest

    if not loaded.tasks:
        # A benchmark whose tasks are produced by its bootstrap has none until it
        # has run, which is the normal state of a fresh checkout.
        problems.append(Problem(
            "no task loaded; a run over zero tasks cannot be scored"
            + (". Its bootstrap has not run here yet" if manifest.data else
               ". Declare them in tasks.yaml or produce them from a bootstrap"),
            fatal=manifest.data is None,
        ))
    for task in loaded.tasks[:200]:
        if not task.workspace or not task.workspace.type:
            problems.append(Problem(f"task {task.task_key!r} declares no workspace source"))
        if not (task.instructions or "").strip():
            problems.append(Problem(f"task {task.task_key!r} has empty instructions"))

    if manifest.prompt:
        template = path / manifest.prompt.template
        if not template.is_file():
            problems.append(Problem(
                f"prompt.template {manifest.prompt.template!r} does not exist; the run "
                f"fails on the first task, after the workspace is prepared"
            ))
        else:
            text = template.read_text(encoding="utf-8")
            for variable in manifest.prompt.variables:
                if variable.required and variable.name not in text:
                    problems.append(Problem(
                        f"prompt declares required value {variable.name!r} and the "
                        f"template never substitutes it"
                    ))

    known = set(eval_registry.ids())
    for stage in (*manifest.evaluation.capture, *manifest.evaluation.verify):
        metric = eval_registry.get(stage.preset)
        if metric is None:
            problems.append(Problem(
                f"evaluation stage {stage.preset!r} is not a metric this deployment "
                f"has; metrics live in plugins/evaluation/"
            ))
            continue
        accepted = {option.key for option in metric.spec.options}
        unknown = sorted(set(stage.config) - accepted)
        if unknown:
            problems.append(Problem(
                f"stage {stage.preset!r} is configured with {unknown}, which the metric "
                f"does not accept; it accepts {sorted(accepted) or 'no options'}"
            ))
    for stage in manifest.evaluation.verify:
        metric = eval_registry.get(stage.preset)
        if metric is not None and not metric.spec.gates:
            problems.append(Problem(
                f"{stage.preset!r} only records, so listing it under evaluation.verify "
                f"cannot fail a task; move it to evaluation.capture"
            ))
    if "file_artifact" in manifest.evaluation.capture_ids and not manifest.evaluation.artifact:
        problems.append(Problem(
            "evaluation.capture includes file_artifact without evaluation.artifact, "
            "so there is no path to capture"
        ))
    expression = manifest.evaluation.passed
    if expression:
        problems.extend(_check_expression(expression, manifest.evaluation.verify))

    return problems


def _check_expression(expression: str, stages) -> list[Problem]:
    """The verdict rule is evaluated with every declared stage passing.

    A rule that cannot be evaluated at all, or that names a stage the benchmark
    does not run, decides nothing and would only be discovered when the first
    task finished.
    """
    from app.evaluation.expressions import evaluate

    passing = {stage.preset: True for stage in stages}
    try:
        evaluate(expression, passing)
    except Exception as exc:
        return [Problem(f"evaluation.passed {expression!r} cannot be evaluated: {exc}")]
    return []


def _check_agent(loaded, path: Path) -> list[Problem]:
    problems: list[Problem] = []
    manifest, impl = loaded.manifest, loaded.impl

    if not manifest.binary:
        problems.append(Problem(
            "no binary declared; without it the platform cannot report the tool as "
            "missing before a run and the failure lands inside the agent's terminal"
        ))
    elif shutil.which(manifest.binary) is None and not manifest.install:
        problems.append(Problem(
            f"{manifest.binary!r} is not installed here and no install command is "
            f"declared, so the dashboard can only say it is absent"
        ))

    unknown = sorted(set(manifest.capabilities) - set(CAPABILITIES))
    if unknown:
        problems.append(Problem(
            f"unknown capabilities {unknown}; the platform honours "
            f"{', '.join(CAPABILITIES)}"
        ))

    wire = str(getattr(impl, "wire", "chat_completions") or "")
    if wire not in WIRES:
        problems.append(Problem(
            f"wire {wire!r} is not a request format the platform can match against a "
            f"provider; use one of {', '.join(WIRES)}"
        ))

    # Every task ends in parse_session, including one whose agent died before
    # writing anything. An adapter that raises or returns the wrong type there
    # fails the task after the model has already been paid for.
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "terminal.log"
        log.write_text("", encoding="utf-8")
        try:
            info = impl.parse_session(None, log)
            if not isinstance(info, SessionInfo):
                problems.append(Problem(
                    f"parse_session returned {type(info).__name__}, not SessionInfo"
                ))
        except Exception as exc:
            problems.append(Problem(
                f"parse_session raised {type(exc).__name__} on an empty log: {exc}"
            ))
    return problems


def _check_evaluation(loaded, path: Path) -> list[Problem]:
    problems: list[Problem] = []
    impl, spec = loaded.impl, loaded.impl.spec

    if not spec.title:
        problems.append(Problem("spec declares no title, so the dashboard can only show the id"))
    if not spec.summary:
        problems.append(Problem("spec declares no summary of what the metric measures"))
    if not spec.requires:
        problems.append(Problem(
            "spec does not say what the metric needs in order to run; an operator then "
            "discovers a missing tool in a failed run", fatal=False))
    if spec.gates and not impl.reason:
        problems.append(Problem(
            "the metric can fail a task and declares no reason code, so its failures "
            "cannot be grouped with anything else", fatal=False))
    for option in spec.options:
        if not option.label:
            problems.append(Problem(f"option {option.key!r} has no label"))
        if option.type == "choice" and not option.choices:
            problems.append(Problem(f"option {option.key!r} is a choice with no choices"))

    if type(impl).measure is EvaluationPlugin.measure:
        return problems + [Problem("measure() is not implemented, so the metric measures nothing")]
    if len(inspect.signature(impl.measure).parameters) != 2:
        problems.append(Problem("measure() must take (ctx, config); the platform calls it with both"))
    try:
        available = impl.availability()
        if not (isinstance(available, tuple) and len(available) == 2 and isinstance(available[0], bool)):
            problems.append(Problem("availability() must return (can_run, reason)"))
        elif not available[0] and not available[1]:
            problems.append(Problem("availability() reports the metric cannot run and gives no reason"))
        elif not available[0] and not loaded.manifest.install:
            problems.append(Problem(
                f"the metric cannot run here ({available[1]}) and the manifest declares no "
                f"install command", fatal=False))
    except Exception as exc:
        problems.append(Problem(f"availability() raised {type(exc).__name__}: {exc}"))
    return problems


def _check_lsp(loaded, path: Path) -> list[Problem]:
    problems: list[Problem] = []
    impl = loaded.impl
    if not loaded.manifest.language:
        problems.append(Problem("no language declared, so no task can select it"))
    try:
        ready = impl.ensure()
        if not (isinstance(ready, tuple) and len(ready) == 2 and isinstance(ready[0], bool)):
            problems.append(Problem("ensure() must return (ready, detail)"))
    except Exception as exc:
        problems.append(Problem(f"ensure() raised {type(exc).__name__}: {exc}"))
    with tempfile.TemporaryDirectory() as tmp:
        try:
            config = impl.server_config(Path(tmp))
            if not isinstance(config, dict):
                problems.append(Problem("server_config() must return a mapping"))
        except Exception as exc:
            problems.append(Problem(f"server_config() raised {type(exc).__name__}: {exc}"))
    return problems


def _safe(impl, name: str, fallback):
    try:
        return getattr(impl, name)() or fallback
    except Exception:
        return fallback


def plugin_dirs(plugins_dir: Path) -> Iterable[Path]:
    """Every plugin directory under a plugins root, in a stable order."""
    for kind in sorted(KINDS):
        base = plugins_dir / kind
        if not base.is_dir():
            continue
        for path in sorted(p for p in base.iterdir() if p.is_dir()):
            if (path / "plugin.yaml").is_file():
                yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.catalog.verify",
        description="Check a plugin against the contracts the platform loads it by.",
    )
    parser.add_argument("plugin", nargs="*", type=Path,
                        help="plugin directory; defaults to every shipped plugin")
    parser.add_argument("--plugins-dir", type=Path, default=None,
                        help="the platform's plugins root (default: ./plugins)")
    args = parser.parse_args(argv)

    shipped = (args.plugins_dir or Path("plugins")).resolve()
    targets = [p.resolve() for p in args.plugin] or list(plugin_dirs(shipped))
    if not targets:
        print(f"no plugin found under {shipped}", file=sys.stderr)
        return 2

    failed = 0
    for target in targets:
        problems = verify_plugin(target, shipped=shipped)
        label = f"{target.parent.name}/{target.name}"
        if not problems:
            print(f"ok    {label}")
            continue
        if any(p.fatal for p in problems):
            failed += 1
        print(f"FAIL  {label}" if any(p.fatal for p in problems) else f"warn  {label}")
        for problem in problems:
            print(f"      {problem}")
    print(f"\n{len(targets) - failed}/{len(targets)} plugins conform")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
