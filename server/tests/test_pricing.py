from __future__ import annotations

from app.api.pricing import Usage, cost_usd, usage_from_result


def test_cost_bills_cache_reads_at_the_cheaper_rate():
    """cacheRead ⊆ input: the cached part must not be billed at prompt price."""
    pricing = {"prompt": "0.00001", "completion": "0.00005", "input_cache_read": "0.000001"}
    usage = Usage(input_tokens=1000, output_tokens=100, cache_read_tokens=800)

    # 200 fresh * 1e-5 + 800 cached * 1e-6 + 100 out * 5e-5 = 0.002 + 0.0008 + 0.005
    assert cost_usd(usage, pricing) == 0.0078

    # without a cache-read rate the provider bills cache reads as prompt
    assert cost_usd(usage, {"prompt": "0.00001", "completion": "0.00005"}) == 1000 * 1e-5 + 100 * 5e-5


def test_cost_is_zero_for_free_models_and_none_without_pricing():
    assert cost_usd(Usage(1000, 500), {"prompt": "0", "completion": "0"}) == 0.0
    assert cost_usd(Usage(1000, 500), None) is None
    assert cost_usd(Usage(1000, 500), {}) is None


def test_cache_read_cannot_exceed_input():
    """A malformed report must not produce negative fresh-input billing."""
    pricing = {"prompt": "0.00001", "completion": "0", "input_cache_read": "0"}
    assert cost_usd(Usage(input_tokens=100, cache_read_tokens=9999), pricing) == 0.0


def test_usage_from_result_reads_metrics():
    result = {"tokensInput": 10, "tokensOutput": 2, "metrics": {"tokensCacheRead": 4}}
    assert usage_from_result(result) == Usage(10, 2, 4)
    assert usage_from_result({}) == Usage(0, 0, 0)


def test_negative_rate_is_not_a_price():
    """OpenRouter publishes -1 for router models ("depends what it picks")."""
    from app.api.pricing import Usage, cost_usd

    usage = Usage(input_tokens=455_643, output_tokens=1_000)
    assert cost_usd(usage, {"prompt": "-1", "completion": "-1"}) is None
    # a real price still computes
    assert cost_usd(usage, {"prompt": "0", "completion": "0"}) == 0.0
