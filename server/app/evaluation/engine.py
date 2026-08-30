"""Score one finished task: prepare, record, gate, decide.

The pipeline is what the benchmark's manifest says it is:

    prepare   the benchmark's own hook, when it declares one, publishing what its
              metrics need through `ctx.shared`
    capture   metrics that record numbers and evidence
    verify    metrics that can fail, in order
    verdict   a boolean expression over the verify stages

Every metric named in the manifest is an evaluation plugin, resolved by id. A
plugin may replace the whole thing with its own `evaluate()`.
"""
from __future__ import annotations

from pathlib import Path

from app.catalog.sdk import EvalContext, EvalOutcome, StageResult
from app.evaluation import expressions
from app.evaluation import registry

def _metric(name: str) -> registry.Metric:
    metric = registry.get(name)
    if metric is None:
        raise KeyError(
            f"no metric {name!r} is installed; metrics live in plugins/evaluation/"
        )
    return metric


def _write_log(ctx: EvalContext, res: StageResult) -> None:
    if not res.log:
        return
    eval_dir = ctx.artifacts_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / f"{res.name.replace('.', '_')}.log").write_text(res.log, encoding="utf-8")


def effective_pipeline(ev, override: dict | None) -> tuple[list[tuple[str, dict]], str]:
    """The shipped verify pipeline with the operator's Settings edits applied.

    An override may retune a stage's options, switch a stage off, add a metric the
    benchmark does not ship, or replace the verdict rule. A stage naming a metric
    this deployment does not have is dropped: an override outlives the plugin it
    was written against, and a stale one must not fail every task in a run.
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

    known = {preset for preset, _ in shipped}
    for stage in override.get("verify", []):
        preset = stage.get("preset")
        if not preset or preset in known or stage.get("enabled") is False:
            continue
        if registry.get(preset) is None:
            continue
        out.append((preset, dict(stage.get("config") or {})))
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
    first_fail: StageResult | None = None

    # prepare — one step, before anything measures, publishing what the metrics
    # read from ctx.shared. Recorded like a stage so a failed preparation is
    # visible, but it decides no verdict of its own.
    if ev.prepare:
        prepared = loaded.hooks.prepare(ctx)
        if prepared is not None:
            prepared.name = ev.prepare
            stages.append(prepared)
            details[prepared.name] = {"ok": prepared.ok, "message": prepared.message,
                                      **(prepared.outputs or {})}
            _write_log(ctx, prepared)
            if not prepared.ok:
                first_fail = prepared

    # capture
    for stage in ev.capture:
        res = _metric(stage.preset).measure(ctx, stage.config)
        stages.append(res)
        metrics.update(res.outputs)
        _write_log(ctx, res)

    # verify
    verify, passed_expr = effective_pipeline(ev, override)
    stage_pass: dict[str, bool] = {}
    for preset, config in verify:
        res = _metric(preset).measure(ctx, config)
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
        reason = (
            first_fail.reason
            or registry.reason_for(first_fail.name)
            or "unknown"
        )
    # session-level failure flags override the reason
    if ctx.session and ctx.session.flags:
        flagged = _flag_reason(ctx.session.flags)
        if flagged in ("provider_error", "model_mismatch"):
            passed, reason = False, flagged
        elif flagged and not passed:
            # the stage that failed is the symptom: an agent that ran out of
            # context left nothing to apply, and `apply_failed` hides why
            reason = flagged

    return EvalOutcome(passed=passed, reason=reason, metrics=metrics, details=details, stages=stages)


def _flag_reason(flags: set[str]) -> str:
    if "model_mismatch" in flags:
        return "model_mismatch"
    if flags & {"auth_wall", "transport_error", "rate_limited"}:
        return "provider_error"
    if "context_limit" in flags:
        # the request was served; the model had no room left to answer in
        return "context_limit"
    return ""


def seed_artifacts(loaded, workspace: Path, task) -> None:
    """Seed a templated output artifact before the agent runs (file_artifact)."""
    ev = loaded.manifest.evaluation
    if "file_artifact" not in ev.capture_ids or ev.artifact is None or not ev.artifact.seed:
        return
    from app.catalog.templating import render
    rel = render(ev.artifact.path, task)
    dest = workspace / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(ev.artifact.template, task), encoding="utf-8")
