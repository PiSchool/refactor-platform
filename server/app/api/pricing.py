"""Model pricing and cost.

Prices come from the provider's own catalog (OpenRouter `/models`), expressed in
USD **per token**. Nothing is hardcoded: a stale price table is worse than none.

Token accounting follows what the agent reports:
  cacheRead ⊆ input   (billed at the cheaper cache-read rate)
  reasoning ⊆ output  (already counted in outputTokens)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0


def _rate(pricing: dict, key: str, fallback: float | None = 0.0) -> float | None:
    """A rate in USD/token, or None when the provider does not publish one.

    OpenRouter prices its routing models (`openrouter/auto` and friends) as `-1`,
    meaning "depends on whichever model the router picks". Multiplying that by a
    token count yields a large negative cost, so a negative rate is not a price.
    """
    raw = pricing.get(key)
    if raw in (None, ""):
        return fallback
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return fallback
    return value if value >= 0 else None


def cost_usd(usage: Usage, pricing: dict | None) -> float | None:
    """What this usage costs on a model. None when the model has no price."""
    if not pricing:
        return None
    prompt = _rate(pricing, "prompt")
    completion = _rate(pricing, "completion")
    if prompt is None or completion is None:
        return None
    # Providers that do not price cache reads separately bill them as prompt.
    cache_read = _rate(pricing, "input_cache_read", prompt)
    if cache_read is None:
        cache_read = prompt

    cached = max(0, min(usage.cache_read_tokens, usage.input_tokens))
    fresh_input = usage.input_tokens - cached
    return fresh_input * prompt + cached * cache_read + usage.output_tokens * completion


def usage_from_result(result: dict) -> Usage:
    """Usage as recorded on a TaskResult (serialized form)."""
    metrics = result.get("metrics") or {}
    return Usage(
        input_tokens=int(result.get("tokensInput") or 0),
        output_tokens=int(result.get("tokensOutput") or 0),
        cache_read_tokens=int(metrics.get("tokensCacheRead") or 0),
    )
