#!/usr/bin/env python3
"""Check the statistics against values that can be worked out by hand.

    python scripts/test_uncertainty.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from uncertainty import bootstrap_diff, holm, mcnemar_exact, wilson  # noqa: E402


def close(a, b, tol=0.05):
    return abs(a - b) <= tol


# Wilson for 15/20, worked through by hand with z = 1.96:
#   centre = (0.75 + z^2/40) / (1 + z^2/20)                    = 0.70972
#   half   = z * sqrt(0.75*0.25/20 + z^2/1600) / (1 + z^2/20)  = 0.17842
# giving 53.1 % to 88.8 %. Note the centre sits below the observed 75 %: Wilson
# shrinks toward 0.5, which is what keeps it honest at the extremes.
lo, hi = wilson(15, 20)
assert close(lo, 53.1, 0.1) and close(hi, 88.8, 0.1), (lo, hi)
assert lo < 75.0 < hi and (lo + hi) / 2 < 75.0, (lo, hi)

# The interval must stay inside [0, 100] where the normal approximation would not.
lo, hi = wilson(100, 100)
assert lo > 90 and close(hi, 100.0), (lo, hi)
lo, hi = wilson(0, 100)
assert close(lo, 0.0) and hi < 10, (lo, hi)

# McNemar with no disagreement is p = 1 however lopsided the rates are.
same = {f"t{i}": True for i in range(50)}
assert mcnemar_exact(same, same)["p_value"] == 1.0

# One discordant task: two-sided exact p = 2 * 0.5 = 1.0. This is the S2-vs-S3
# case, and the reason that comparison cannot support a claim.
a = {"t1": True, "t2": True, "t3": False}
b = {"t1": True, "t2": False, "t3": False}
m = mcnemar_exact(a, b)
assert (m["discordant_a_only"], m["discordant_b_only"]) == (1, 0), m
assert close(m["p_value"], 1.0), m

# Ten discordant tasks all favouring one side: p = 2 * 0.5^10 = 0.001953.
a = {f"t{i}": True for i in range(10)}
b = {f"t{i}": False for i in range(10)}
assert close(mcnemar_exact(a, b)["p_value"], 0.001953, 1e-5)

# Only shared tasks are compared; extra tasks on one side are ignored.
assert mcnemar_exact({**a, "extra": False}, b)["n_paired"] == 10

# The bootstrap interval for a uniform +100 pp difference is degenerate at +100.
lo, hi = bootstrap_diff(a, b, draws=200)
assert close(lo, 100.0) and close(hi, 100.0), (lo, hi)

# Holm: the smallest p is multiplied by n, and the sequence never decreases.
adj = holm([0.01, 0.04, 0.03])
assert close(adj[0], 0.03, 1e-9), adj
assert adj[1] >= adj[2] >= adj[0], adj
assert all(v <= 1.0 for v in holm([0.5, 0.6, 0.7]))

print("uncertainty: all checks passed")
