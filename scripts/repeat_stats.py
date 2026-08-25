#!/usr/bin/env python3
"""Score a repeated-run campaign: is the effect stable, or was one run lucky?

`scripts/uncertainty.py` quantifies sampling uncertainty over the 100 benchmark
tasks while holding the run fixed. That is the wrong tool for the question the
reviewers actually asked — whether a stochastic agent produces the same answer
twice — so this scores the other axis: variation *between* repeated runs of the
same configuration.

Four things, because each answers a different objection:

* **Per-run rates, mean and standard deviation** — the spread a single number hides.
* **A 95 % interval on the mean**, from Student's t with n-1 degrees of freedom.
  With five runs the normal approximation is optimistic; t is the honest choice.
* **pass@k** — the share of tasks solved in at least one of k runs. The gap
  between pass@1 and pass@k is exactly how much of the score is luck.
* **Per-task flip rate** — how many tasks change verdict between runs. A large
  effect built on tasks that flip every run is not a stable effect.

Consumes the JSON that `campaign.py` writes.

    python scripts/repeat_stats.py --campaign repeat_campaign.json
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from uncertainty import wilson  # noqa: E402

#: Two-sided 95 % critical values of Student's t, by degrees of freedom. Small
#: campaigns only; beyond this the normal value is close enough.
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
       8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 15: 2.131, 20: 2.086}


def t_critical(df: int) -> float:
    if df <= 0:
        return float("nan")
    if df in T95:
        return T95[df]
    return T95[max(k for k in T95 if k <= df)] if df < 20 else 1.96


def mean_interval(values: list[float]) -> tuple[float, float, float, float]:
    """Mean, sample SD, and the 95 % t-interval around the mean."""
    n = len(values)
    mean = statistics.fmean(values)
    if n < 2:
        return mean, 0.0, mean, mean
    sd = statistics.stdev(values)
    half = t_critical(n - 1) * sd / math.sqrt(n)
    return mean, sd, mean - half, mean + half


def pass_at_k(per_task: list[dict[str, bool]]) -> dict[str, float]:
    """pass@1 (mean over runs) and pass@k (solved at least once)."""
    if not per_task:
        return {}
    tasks = sorted(set().union(*(set(r) for r in per_task)))
    at_least_once = sum(1 for t in tasks if any(r.get(t) for r in per_task))
    every_time = sum(1 for t in tasks if all(r.get(t) for r in per_task))
    per_run = [100 * sum(r.get(t, False) for t in tasks) / len(tasks) for r in per_task]
    return {
        "tasks": len(tasks),
        "k": len(per_task),
        "pass@1": round(statistics.fmean(per_run), 1),
        "pass@k": round(100 * at_least_once / len(tasks), 1),
        "solved_every_run": round(100 * every_time / len(tasks), 1),
        "flipped": at_least_once - every_time,
        "flip_rate": round(100 * (at_least_once - every_time) / len(tasks), 1),
    }


def paired_differences(a: list[dict[str, bool]], b: list[dict[str, bool]]) -> list[float]:
    """Per-repeat difference in pass rate, pairing run i of A with run i of B.

    Pairing by repeat index rather than pooling keeps each difference a
    within-round comparison, which is what the campaign was designed to produce.
    """
    out = []
    for run_a, run_b in zip(a, b):
        shared = sorted(set(run_a) & set(run_b))
        if not shared:
            continue
        ra = 100 * sum(run_a[t] for t in shared) / len(shared)
        rb = 100 * sum(run_b[t] for t in shared) / len(shared)
        out.append(ra - rb)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--campaign", required=True, type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path)
    args = ap.parse_args()

    record = json.loads(args.campaign.read_text(encoding="utf-8"))
    runs = record.get("runs", [])
    if not runs:
        raise SystemExit(f"{args.campaign} records no runs yet")

    # A repeat may be recorded as several batches, so that a restart costs one
    # batch rather than the whole pass. A batch is not a repeat: merge them back
    # before anything is scored, or the spread is measured over the wrong thing.
    merged: dict[tuple[str, int], dict] = {}
    for r in runs:
        key = (r["setup"], r["repeat"])
        entry = merged.setdefault(key, {"setup": r["setup"], "repeat": r["repeat"],
                                        "passed": 0, "total": 0, "perTask": {}})
        entry["passed"] += r["passed"]
        entry["total"] += r["total"]
        entry["perTask"].update(r["perTask"])
    for entry in merged.values():
        entry["rate"] = round(100 * entry["passed"] / entry["total"], 1) if entry["total"] else None

    by_setup: dict[str, list[dict]] = {}
    for entry in merged.values():
        by_setup.setdefault(entry["setup"], []).append(entry)
    for entries in by_setup.values():
        entries.sort(key=lambda e: e["repeat"])

    report: dict = {"model": runs[0].get("model"), "setups": {}, "comparison": None}

    print(f"model: {runs[0].get('model')}\n")
    for setup, entries in sorted(by_setup.items()):
        rates = [e["rate"] for e in entries if e.get("rate") is not None]
        if not rates:
            continue
        mean, sd, lo, hi = mean_interval(rates)
        pk = pass_at_k([e["perTask"] for e in entries])
        report["setups"][setup] = {"runs": len(rates), "rates": rates,
                                   "mean": round(mean, 1), "sd": round(sd, 2),
                                   "ci95": [round(lo, 1), round(hi, 1)], **pk}
        print(f"{setup}")
        print(f"  rates over {len(rates)} runs : {rates}")
        print(f"  mean {mean:.1f}%  SD {sd:.2f}  95% CI [{lo:.1f}, {hi:.1f}]")
        if pk:
            print(f"  pass@1 {pk['pass@1']}%   pass@{pk['k']} {pk['pass@k']}%   "
                  f"solved every run {pk['solved_every_run']}%")
            print(f"  flipped between runs: {pk['flipped']}/{pk['tasks']} tasks "
                  f"({pk['flip_rate']}%)")
        # A single run's own task-sampling interval, for contrast with the spread above.
        first = entries[0]
        w = wilson(first["passed"], first["total"])
        print(f"  (run 1 alone: {first['passed']}/{first['total']}, "
              f"Wilson CI [{w[0]:.1f}, {w[1]:.1f}])\n")

    if "s2_rag_ast" in by_setup and "s2_rag_naive" in by_setup:
        ast = [e["perTask"] for e in by_setup["s2_rag_ast"]]
        naive = [e["perTask"] for e in by_setup["s2_rag_naive"]]
        diffs = paired_differences(ast, naive)
        if diffs:
            mean, sd, lo, hi = mean_interval(diffs)
            wins = sum(1 for d in diffs if d > 0)
            report["comparison"] = {
                "per_repeat_delta_pp": [round(d, 1) for d in diffs],
                "mean_delta_pp": round(mean, 1), "sd": round(sd, 2),
                "ci95": [round(lo, 1), round(hi, 1)],
                "ast_wins": wins, "rounds": len(diffs),
            }
            print("AST chunking vs naive chunking, paired by repeat")
            print(f"  per-repeat delta : {[round(d,1) for d in diffs]}")
            print(f"  mean {mean:+.1f} pp  SD {sd:.2f}  95% CI [{lo:+.1f}, {hi:+.1f}]")
            print(f"  AST ahead in {wins} of {len(diffs)} rounds")
            if lo > 0:
                print("  the interval excludes zero: the effect holds across runs")
            else:
                print("  the interval includes zero: not separable at this sample size")

    if args.out:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
