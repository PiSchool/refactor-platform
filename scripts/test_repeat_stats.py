#!/usr/bin/env python3
"""Check the repeated-run statistics against values worked out by hand.

    python scripts/test_repeat_stats.py
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from repeat_stats import mean_interval, pass_at_k, paired_differences, t_critical  # noqa: E402

# Rates [80, 84, 86, 88, 92], worked through by hand:
#   mean       = 86
#   deviations = -6, -2, 0, 2, 6 -> squares 36, 4, 0, 4, 36 = 80; /(n-1)=4 -> 20
#   SD         = sqrt(20) = 4.47214
#   half-width = t(4) * SD / sqrt(5) = 2.776 * 2.0 = 5.552
#   CI         = [80.448, 91.552]
mean, sd, lo, hi = mean_interval([80, 84, 86, 88, 92])
assert abs(mean - 86) < 1e-9, mean
assert abs(sd - math.sqrt(20)) < 1e-9, sd
assert abs(lo - 80.448) < 0.01 and abs(hi - 91.552) < 0.01, (lo, hi)

# The t-interval must be wider than the normal one at this sample size; using
# 1.96 with five runs is the optimism this table exists to avoid.
normal_half = 1.96 * sd / math.sqrt(5)
assert (hi - lo) / 2 > normal_half, "t-interval should exceed the normal interval"

# One run has no spread to report, and must not invent one.
assert mean_interval([73.0]) == (73.0, 0.0, 73.0, 73.0)
assert t_critical(4) == 2.776 and t_critical(1) == 12.706

# pass@k over three runs: A passes always, B once, C never.
#   pass@1 = mean per-run rate = (2/3 + 1/3 + 1/3)/3 = 44.4 %
#   pass@3 = solved at least once = 2/3 = 66.7 %
#   solved every run = 1/3 = 33.3 %, and exactly one task (B) flips
pk = pass_at_k([{"A": True, "B": True, "C": False},
                {"A": True, "B": False, "C": False},
                {"A": True, "B": False, "C": False}])
assert pk["pass@1"] == 44.4 and pk["pass@k"] == 66.7, pk
assert pk["solved_every_run"] == 33.3 and pk["flipped"] == 1, pk
assert pk["k"] == 3 and pk["tasks"] == 3, pk

# A configuration that never varies has no flips, and pass@1 equals pass@k.
steady = pass_at_k([{"A": True, "B": False}] * 4)
assert steady["flipped"] == 0 and steady["pass@1"] == steady["pass@k"] == 50.0, steady

# Differences pair run i against run i, rather than pooling every combination.
d = paired_differences([{"A": True, "B": True}, {"A": True, "B": False}],
                       [{"A": True, "B": False}, {"A": False, "B": False}])
assert d == [50.0, 50.0], d

# Unequal run counts pair only as far as both configurations reach.
assert len(paired_differences([{"A": True}] * 3, [{"A": False}] * 2)) == 2

print("repeat_stats: all checks passed")
