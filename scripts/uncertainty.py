#!/usr/bin/env python3
"""Uncertainty and paired significance for every comparison the study reports.

Reviewers asked for the two things a single pass rate cannot supply: an interval
around each number, and a test that says whether a gap between two numbers is
larger than noise.

Both come out of the per-task verdicts already in `docs/exports/`, with no reruns:

* **Wilson score interval** — a 95% interval for one pass rate. Preferred over
  the textbook normal interval, which misbehaves near 0 % and 100 % and can run
  past the ends of the scale (Brown, Cai and DasGupta, 2001).
* **McNemar exact test** — every configuration ran *the same* benchmark tasks, so
  the comparisons are paired. Only the tasks where the two disagree carry
  information; the count of those splits under the null like a fair coin, and the
  exact binomial tail is the p-value (McNemar, 1947). An unpaired two-proportion
  test would throw away the pairing and overstate the uncertainty.
* **Paired bootstrap** — a 95 % interval for the *difference*, resampling tasks
  (not runs), which is the quantity the paper's claims are actually about.

These describe sampling uncertainty over the 100-task benchmark, holding the run
fixed. They do not describe run-to-run variation of a stochastic agent; that
needs repeated runs, reported separately by `scripts/repeat_runs.py`.

    python scripts/uncertainty.py --archive docs/exports --out docs/exports
    python scripts/uncertainty.py --archive docs/exports --latex
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import import_study_runs as I  # noqa: E402
from matched_subset_analysis import crash_prefix  # noqa: E402

Z95 = 1.959963984540054
BOOTSTRAP = 10000
SEED = 20260824


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #
def wilson(passed: int, total: int, z: float = Z95) -> tuple[float, float]:
    """95 % Wilson score interval for a binomial proportion, as percentages."""
    if total == 0:
        return (0.0, 0.0)
    p, z2 = passed / total, z * z
    centre = (p + z2 / (2 * total)) / (1 + z2 / total)
    half = z * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total)) / (1 + z2 / total)
    return (100 * max(0.0, centre - half), 100 * min(1.0, centre + half))


def mcnemar_exact(a: dict[str, bool], b: dict[str, bool]) -> dict:
    """Two-sided exact McNemar over the tasks both configurations ran.

    `b_only` counts tasks the first passed and the second failed, `c_only` the
    reverse. Concordant tasks tell us nothing about which is better, so the test
    conditions on the discordant ones.
    """
    shared = sorted(set(a) & set(b))
    b_only = sum(1 for t in shared if a[t] and not b[t])
    c_only = sum(1 for t in shared if b[t] and not a[t])
    n = b_only + c_only
    if n == 0:
        p = 1.0
    else:
        k = min(b_only, c_only)
        tail = sum(math.comb(n, i) for i in range(k + 1)) * (0.5 ** n)
        p = min(1.0, 2 * tail)
    return {"n_paired": len(shared), "discordant_a_only": b_only,
            "discordant_b_only": c_only, "p_value": p}


def bootstrap_diff(a: dict[str, bool], b: dict[str, bool],
                   draws: int = BOOTSTRAP, seed: int = SEED) -> tuple[float, float]:
    """Percentile 95 % interval for (rate_a - rate_b) in points, resampling tasks."""
    shared = sorted(set(a) & set(b))
    if not shared:
        return (0.0, 0.0)
    pairs = [(a[t], b[t]) for t in shared]
    rng, n, diffs = random.Random(seed), len(pairs), []
    for _ in range(draws):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        diffs.append(100 * (sum(x for x, _ in sample) - sum(y for _, y in sample)) / n)
    diffs.sort()
    return (diffs[int(0.025 * draws)], diffs[int(0.975 * draws) - 1])


def stars(p: float) -> str:
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."


def holm(pvalues: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, in the input order.

    The study makes a family of comparisons off one benchmark, so an unadjusted
    0.05 threshold would expect a false positive roughly every twenty tests. Holm
    controls the family-wise error rate without assuming the tests are
    independent, which Bonferroni-Sidak would.
    """
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(pvalues) - rank) * pvalues[i])
        adjusted[i] = min(1.0, running)
    return adjusted


# --------------------------------------------------------------------------- #
# loading per-task verdicts
# --------------------------------------------------------------------------- #
def _verdict(row: dict, benchmark: str) -> bool | None:
    v = I.truthy(I.pick(row, I.PASSED))
    if v is not None:
        return v
    if benchmark == "swe":
        ast, build = I.truthy(I.pick(row, I.AST_OK)), I.truthy(I.pick(row, I.BUILD_OK))
        return None if ast is None or build is None else (ast and build)
    v = I.truthy(I.pick(row, I.TESTS_OK))
    if v is not None:
        return v
    # The naive-chunking sweep records its verdict as a run status; a timeout is
    # a failure, not a missing observation.
    status = (row.get("status") or "").strip().lower()
    return {"success": True, "failed": False, "timed_out": False}.get(status)


def _from_archive(runs: dict, title: str, benchmark: str = "refbench",
                  where: tuple[str, str] | None = None) -> dict[str, bool]:
    out = {}
    for row in runs[title]["rows"]:
        if where and (row.get(where[0]) or "").strip() != where[1]:
            continue
        task, v = I.pick(row, I.TASK), _verdict(row, benchmark)
        if task and v is not None:
            out[task] = v
    return out


def _from_result_column(path: pathlib.Path, order: list[str]) -> dict[str, bool]:
    """Two LSP-ablation exports carry PASSED/FAILED in a `Result` column, and one
    of them has task ids truncated to a timestamped stub. Both list the benchmark
    in its canonical order, so pair by position against a run whose ids are
    intact — and refuse rather than guess if the lengths disagree."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    head = next(i for i, line in enumerate(lines) if line.startswith("#,"))
    rows = [r for r in csv.DictReader(io.StringIO("\n".join(lines[head:])))
            if (r.get("Result") or "").strip()]
    if len(rows) != len(order):
        raise SystemExit(f"{path.name}: {len(rows)} rows against {len(order)} task ids")
    return {task: (r["Result"].strip() == "PASSED") for task, r in zip(order, rows)}


def load(archive: pathlib.Path) -> dict[str, dict[str, bool]]:
    """Every configuration the paper reports, as task id -> passed."""
    runs = {r["title"]: r for r in I.parse_appendix(archive / "appendix_per_task.md")}
    csvs = archive / "csv"
    cfg: dict[str, dict[str, bool]] = {}

    # --- RefactorBench, qwen3.6-flash ablation (Table 1) ---------------------
    cfg["S1 descriptive +LSP"] = _from_archive(runs, "Run 1: qwen3.6-flash S1 descriptive RefactorBench")
    cfg["S1 base +LSP"] = _from_archive(runs, "qwen3.6-flash S1 base+LSP RefactorBench")
    order = list(cfg["S1 descriptive +LSP"])
    cfg["S1 lazy +LSP"] = _from_result_column(csvs / "s1_lazy_lsp_refbench.csv", order)
    cfg["S1 lazy -LSP"] = _from_result_column(csvs / "s1_lazy_nolsp_refbench.csv", order)

    for mode in ("descriptive", "base", "lazy"):
        cfg[f"S2-AST {mode}"] = _from_archive(runs, f"qwen3.6-flash S2-RAG {mode} RefactorBench")
    # The all-modes sweep is the authority for naive chunking. `Run 3:
    # qwen3.6-flash S2-naive desc` is *not* a second descriptive run: it scores
    # 44, carries the base-mode pipeline id, and is the base arm under a wrong
    # filename. Reading it as descriptive would understate AST's margin by 13 pp.
    for mode in ("descriptive", "base", "lazy"):
        cfg[f"S2-naive {mode}"] = _from_archive(
            runs, "Run 2: qwen3.6-flash S2-naive all modes RefactorBench",
            where=("mode", mode))

    # --- multi-agent ---------------------------------------------------------
    s3 = _from_archive(runs, "qwen3.6-flash S3 subagent desc RefactorBench")
    rows = [(t, float(r["duration_seconds"] or 0), r["passed"].strip().lower() == "true")
            for r in runs["qwen3.6-flash S3 subagent desc RefactorBench"]["rows"]
            for t in [r["task_id"]]]
    executed = crash_prefix(rows)
    cfg["S3 sub-agents descriptive (executed)"] = {t: p for t, _, p in rows[:executed]}
    cfg["S3 sub-agents descriptive (all dispatched)"] = s3
    cfg["S3 CAO base"] = _from_archive(runs, "qwen3.6-flash S3 CAO base RefactorBench")

    # --- cross-model (Table 2) ----------------------------------------------
    for model, s1_title, s2_title in (
        ("deepseek-v4-pro", "Run 4: deepseek-v4-pro S1 desc RefactorBench",
         "deepseek-v4-pro S2-RAG descriptive RefactorBench"),
        ("minimax-m3", "Run 5: minimax-m3 S1 desc RefactorBench",
         "minimax-m3 S2-RAG descriptive RefactorBench"),
        ("kimi-k2.6", "Run 6: kimi-k2.6 S1 desc RefactorBench",
         "kimi-k2.6 S2-RAG descriptive RefactorBench"),
    ):
        cfg[f"{model} S1"] = _from_archive(runs, s1_title)
        cfg[f"{model} S2-AST"] = _from_archive(runs, s2_title)
    cfg["qwen3.6-flash S1"] = cfg["S1 descriptive +LSP"]
    cfg["qwen3.6-flash S2-AST"] = cfg["S2-AST descriptive"]

    # --- SWE-Refactor --------------------------------------------------------
    cfg["gpt-5-mini S1 (SWE)"] = _from_archive(runs, "Run 16: gpt-5-mini S1 default SWE-Refactor", "swe")
    cfg["gpt-5-mini S1-eval (SWE)"] = _from_archive(runs, "Run 17: gpt-5-mini S1-eval SWE-Refactor", "swe")
    cfg["minimax-m3 S1 (SWE)"] = _from_archive(runs, "Run 14: minimax-m3 S1 SWE-Refactor", "swe")
    return {k: v for k, v in cfg.items() if v}


# --------------------------------------------------------------------------- #
# the comparisons the paper makes
# --------------------------------------------------------------------------- #
COMPARISONS = [
    ("AST vs naive chunking (descriptive)", "S2-AST descriptive", "S2-naive descriptive"),
    ("AST vs naive chunking (base)", "S2-AST base", "S2-naive base"),
    ("AST vs naive chunking (lazy)", "S2-AST lazy", "S2-naive lazy"),
    ("S2-AST vs S1 (descriptive)", "S2-AST descriptive", "S1 descriptive +LSP"),
    ("S2-AST vs S1 (base)", "S2-AST base", "S1 base +LSP"),
    ("S2-AST vs S1 (lazy)", "S2-AST lazy", "S1 lazy +LSP"),
    ("S2-naive vs S1 (descriptive)", "S2-naive descriptive", "S1 descriptive +LSP"),
    ("LSP on vs off (lazy)", "S1 lazy +LSP", "S1 lazy -LSP"),
    ("S2-AST vs S3 sub-agents (matched 26)", "S2-AST descriptive", "S3 sub-agents descriptive (executed)"),
    ("S1 vs S3 sub-agents (matched 26)", "S1 descriptive +LSP", "S3 sub-agents descriptive (executed)"),
    ("S2-AST vs S3 CAO (base, full 100)", "S2-AST base", "S3 CAO base"),
    ("S1 vs S3 CAO (base, full 100)", "S1 base +LSP", "S3 CAO base"),
    ("deepseek-v4-pro S2 vs S1", "deepseek-v4-pro S2-AST", "deepseek-v4-pro S1"),
    ("minimax-m3 S2 vs S1", "minimax-m3 S2-AST", "minimax-m3 S1"),
    ("kimi-k2.6 S2 vs S1", "kimi-k2.6 S2-AST", "kimi-k2.6 S1"),
    ("qwen3.6-flash S2 vs S1", "qwen3.6-flash S2-AST", "qwen3.6-flash S1"),
    ("gpt-5-mini S1-eval vs S1 (SWE, matched)", "gpt-5-mini S1-eval (SWE)", "gpt-5-mini S1 (SWE)"),
]


def analyse(cfg: dict[str, dict[str, bool]]) -> dict:
    rates = {}
    for name, d in sorted(cfg.items()):
        passed, total = sum(d.values()), len(d)
        lo, hi = wilson(passed, total)
        rates[name] = {"passed": passed, "total": total,
                       "rate": round(100 * passed / total, 1),
                       "ci95": [round(lo, 1), round(hi, 1)]}

    tests = []
    for label, a, b in COMPARISONS:
        if a not in cfg or b not in cfg:
            continue
        m = mcnemar_exact(cfg[a], cfg[b])
        lo, hi = bootstrap_diff(cfg[a], cfg[b])
        shared = sorted(set(cfg[a]) & set(cfg[b]))
        ra = 100 * sum(cfg[a][t] for t in shared) / len(shared)
        rb = 100 * sum(cfg[b][t] for t in shared) / len(shared)
        tests.append({"comparison": label, "a": a, "b": b,
                      "rate_a_on_shared": round(ra, 1), "rate_b_on_shared": round(rb, 1),
                      "delta_pp": round(ra - rb, 1),
                      "delta_ci95": [round(lo, 1), round(hi, 1)],
                      "significance": stars(m["p_value"]), **m})

    for t, adj in zip(tests, holm([t["p_value"] for t in tests])):
        t["p_holm"] = adj
        t["significance_holm"] = stars(adj)

    return {"rates": rates, "comparisons": tests,
            "method": {"interval": "Wilson score, 95%", "test": "McNemar exact, two-sided",
                       "multiplicity": f"Holm-Bonferroni over the {len(tests)} comparisons",
                       "delta_interval": f"paired bootstrap over tasks, {BOOTSTRAP} draws, seed {SEED}"}}


def as_latex(report: dict) -> str:
    out = [r"% Generated by scripts/uncertainty.py -- do not edit by hand.",
           r"\begin{tabular}{llrr}", r"\toprule",
           r"Comparison & $\Delta$ (pp) & 95\% CI & $p$ \\", r"\midrule"]
    for t in report["comparisons"]:
        p = t["p_value"]
        ptxt = r"$<$0.001" if p < 0.001 else f"{p:.3f}"
        lo, hi = t["delta_ci95"]
        out.append(f"{t['comparison'].replace('%', r'\%')} & {t['delta_pp']:+.1f} & "
                   f"[{lo:+.1f}, {hi:+.1f}] & {ptxt} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=pathlib.Path, default=pathlib.Path("docs/exports"))
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()

    report = analyse(load(args.archive))

    print(f"{'configuration':44s} {'pass':>10s}  {'rate':>6s}  95% CI")
    for name, r in report["rates"].items():
        print(f"{name:44s} {r['passed']:4d}/{r['total']:<5d} {r['rate']:5.1f}%  "
              f"[{r['ci95'][0]:.1f}, {r['ci95'][1]:.1f}]")
    print(f"\n{'comparison':42s} {'delta':>7s}  {'95% CI':>16s}  {'b/c':>7s} {'p':>10s}  p(Holm)")
    for t in report["comparisons"]:
        lo, hi = t["delta_ci95"]
        print(f"{t['comparison']:42s} {t['delta_pp']:+6.1f}pp  [{lo:+5.1f},{hi:+6.1f}]  "
              f"{t['discordant_a_only']:3d}/{t['discordant_b_only']:<3d} "
              f"{t['p_value']:10.4g}  {t['p_holm']:.4g} {t['significance_holm']}")

    if args.latex:
        print("\n" + as_latex(report))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        path = args.out / "uncertainty.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
