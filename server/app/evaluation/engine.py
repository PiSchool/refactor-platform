"""Compose a benchmark's capture + verify pipeline over a shared EvalContext.

Stage resolution: a name containing '.' is a plugin-defined stage
(benchmark.hooks.stages()); otherwise a core preset. `passed` is a boolean
expression over verify-stage names. A plugin may override the whole thing with
a Python evaluate().
"""
from __future__ import annotations

from pathlib import Path

from app.catalog.sdk import EvalContext, EvalOutcome, StageResult
from app.evaluation import expressions
from app.evaluation.presets import CORE_PRESETS, REASON_BY_STAGE


def _resolve_stage(name: str, hooks):
    if "." in name:
        stages = hooks.stages()
        if name not in stages:
            raise KeyError(f"plugin stage not registered: {name}")
        return stages[name], True
    if name not in CORE_PRESETS:
        raise KeyError(f"unknown preset: {name}")
    return CORE_PRESETS[name].run, False


def _write_log(ctx: EvalContext, res: StageResult) -> None:
    if not res.log:
        return
    eval_dir = ctx.artifacts_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / f"{res.name.replace('.', '_')}.log").write_text(res.log, encoding="utf-8")


def effective_pipeline(ev, override: dict | None) -> tuple[list[tuple[str, dict]], str]:
    """The shipped verify pipeline with the operator's Settings edits applied.

    An override may retune a stage's `config`, disable a stage, or replace the
    `passed` expression. Stages the plugin does not ship are ignored — the
    manifest stays the source of truth for *what can* run.
    """
    shipped = [(s.preset, dict(s.config)) for s in ev.verify]
    passed = ev.passed
    if not override:
        return shipped, passed

    by_preset = {s.get("preset"): s for s in override.get("verify", []) if s.get("preset")}
    out: list[tuple[str, dict]] = []
    for preset, config in shipped:
        edit = by_preset.get(preset)
        if edit is None:
            out.append((preset, config))
            continue
        if edit.get("enabled") is False:
            continue
        out.append((preset, {**config, **(edit.get("config") or {})}))
    return out, (override.get("passed") or passed)


def evaluate(loaded, ctx: EvalContext, override: dict | None = None) -> EvalOutcome:
    # plugin full override
    plugin_outcome = loaded.hooks.evaluate(ctx)
    if plugin_outcome is not None:
        return plugin_outcome

    manifest = loaded.manifest
    ev = manifest.evaluation
    stages: list[StageResult] = []
    metrics: dict = {}
    details: dict = {}

    # capture
    for name in ev.capture:
        fn, _ = _resolve_stage(name, loaded.hooks)
        res = fn(ctx, {} if name != "file_artifact" else _artifact_cfg(ev))
        stages.append(res)
        metrics.update(res.outputs)
        _write_log(ctx, res)

    # verify
    verify, passed_expr = effective_pipeline(ev, override)
    stage_pass: dict[str, bool] = {}
    first_fail: StageResult | None = None
    for preset, config in verify:
        fn, _is_plugin = _resolve_stage(preset, loaded.hooks)
        res = fn(ctx, config)
        stages.append(res)
        stage_pass[res.name] = res.ok
        # a stage's outputs (test counts, applied files, …) belong with its
        # verdict — dropping them left the CSV re-parsing English messages
        details[res.name] = {"ok": res.ok, "message": res.message, **(res.outputs or {})}
        _write_log(ctx, res)
        if not res.ok and first_fail is None:
            first_fail = res

    passed = expressions.evaluate(passed_expr, stage_pass)
    reason = ""
    if not passed and first_fail is not None:
        reason = first_fail.reason or REASON_BY_STAGE.get(first_fail.name, "unknown")
    # session-level failure flags override the reason
    if ctx.session and ctx.session.flags:
        reason = _flag_reason(ctx.session.flags) or reason
        if reason in ("provider_error", "model_mismatch"):
            passed = False

    return EvalOutcome(passed=passed, reason=reason, metrics=metrics, details=details, stages=stages)


def _flag_reason(flags: set[str]) -> str:
    if "model_mismatch" in flags:
        return "model_mismatch"
    if flags & {"auth_wall", "transport_error", "rate_limited"}:
        return "provider_error"
    return ""


def _artifact_cfg(ev) -> dict:
    if ev.artifact is None:
        return {}
    return {"path": ev.artifact.path}


def seed_artifacts(loaded, workspace: Path, task) -> None:
    """Seed a templated output artifact before the agent runs (file_artifact)."""
    ev = loaded.manifest.evaluation
    if "file_artifact" not in ev.capture or ev.artifact is None or not ev.artifact.seed:
        return
    from app.evaluation.render import render
    rel = render(ev.artifact.path, task)
    dest = workspace / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(ev.artifact.template, task), encoding="utf-8")
