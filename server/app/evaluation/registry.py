"""Every measurement this deployment can run, by id.

A measurement is an evaluation plugin: one directory under `plugins/evaluation/`,
whose name is the metric's id. There is no second kind. A benchmark references
ids in its manifest and configures them; it never defines one.

Discovery rebuilds this table wholesale, so a plugin that is removed, renamed or
fails to load leaves nothing behind.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.catalog.sdk import EvaluationPlugin, MetricSpec, StageResult

ID_RULE = "lower-case letters, digits and underscores, starting with a letter"


@dataclass(frozen=True)
class Metric:
    """One measurement, together with where it came from and whether it can run."""

    id: str
    impl: EvaluationPlugin
    plugin_dir: Path

    @property
    def spec(self) -> MetricSpec:
        return self.impl.spec

    @property
    def reason(self) -> str:
        """The failure code recorded when this metric fails."""
        return self.impl.reason

    def availability(self) -> tuple[bool, str]:
        try:
            return self.impl.availability()
        except Exception as exc:                  # a plugin defect is not an outage
            return False, f"availability check failed: {exc}"

    def measure(self, ctx, config: dict) -> StageResult:
        result = self.impl.measure(ctx, dict(config or {}))
        if not isinstance(result, StageResult):
            raise TypeError(f"metric {self.id!r} returned {type(result).__name__}, not StageResult")
        # The id is authoritative: a metric never names its own recorded stage,
        # so evidence and the pipeline that produced it cannot disagree.
        result.name = self.id
        return result


_METRICS: dict[str, Metric] = {}


def reset() -> None:
    _METRICS.clear()


def register(metric: Metric) -> None:
    _METRICS[metric.id] = metric


def all_metrics() -> dict[str, Metric]:
    return dict(_METRICS)


def get(metric_id: str) -> Metric | None:
    return _METRICS.get(metric_id)


def ids() -> list[str]:
    return sorted(_METRICS)


def reason_for(metric_id: str) -> str:
    metric = _METRICS.get(metric_id)
    return metric.reason if metric else ""


def spec_for(metric_id: str) -> MetricSpec | None:
    metric = _METRICS.get(metric_id)
    return metric.spec if metric else None
