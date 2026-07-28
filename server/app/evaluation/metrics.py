"""The metric table as the API serves it.

One shape per metric: what it measures, what it needs, whether it can decide a
verdict, what it records, the options it accepts, and whether this deployment can
run it. The dashboard reads this, so an operator never has to open a plugin's
source to find out what a stage means.
"""
from __future__ import annotations

from app.evaluation import registry


def _option(option) -> dict:
    return {
        "key": option.key,
        "label": option.label,
        "type": option.type,
        "default": option.default,
        "help": option.help,
        "unit": option.unit,
        "choices": list(option.choices),
    }


def _entry(metric: registry.Metric) -> dict:
    available, detail = metric.availability()
    spec = metric.spec
    return {
        "id": metric.id,
        "title": spec.title or metric.id,
        "summary": spec.summary,
        # Whether a stage decides the verdict follows from where the benchmark
        # puts it: capture stages record, verify stages gate. `gates` is what the
        # metric itself can do — a recorded-only metric always reports success.
        "gates": bool(spec.gates),
        "requires": spec.requires,
        "reason": metric.reason,
        "mutatesWorkspace": bool(spec.mutates_workspace),
        "outputs": list(spec.outputs),
        "options": [_option(option) for option in spec.options],
        "available": available,
        "unavailable": "" if available else detail,
    }


def preparation(name: str, spec) -> dict:
    """A benchmark's preparation step, in the shape the pipeline is drawn from.

    It is not a metric — it has no id in the metric table and no options an
    operator can retune — but it is the pipeline's first step and reads the same
    way as the rest of it.
    """
    return {
        "id": name,
        "title": spec.title or name,
        "summary": spec.summary,
        "gates": False,
        "requires": spec.requires,
        "reason": "",
        "mutatesWorkspace": bool(spec.mutates_workspace),
        "outputs": list(spec.outputs),
        "options": [],
        "available": True,
        "unavailable": "",
    }


def catalogue() -> dict[str, dict]:
    """Every metric a benchmark manifest may reference here."""
    return {metric_id: _entry(metric) for metric_id, metric in registry.all_metrics().items()}


def describe(metric_id: str, catalogue: dict[str, dict]) -> dict:
    """The catalogue entry, or a placeholder naming the metric that is missing.

    A manifest may reference a metric a later deployment no longer installs.
    Saying so in place is more useful than an empty row, and the run itself fails
    on the missing stage.
    """
    entry = catalogue.get(metric_id)
    if entry is not None:
        return entry
    return {
        "id": metric_id,
        "title": metric_id,
        "summary": "",
        "gates": True,
        "requires": "",
        "reason": "",
        "mutatesWorkspace": False,
        "outputs": [],
        "options": [],
        "available": False,
        "unavailable": f"no metric {metric_id!r} is installed; metrics live in plugins/evaluation/",
    }
