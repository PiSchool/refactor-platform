#!/usr/bin/env python3
"""What a repeated-run campaign would cost, priced from tokens actually spent.

Repeated runs are the only way to put an interval around run-to-run variation of
a stochastic agent, and the first question is always what that costs. This
prices each candidate plan from the per-task token counts recorded in
`docs/exports/appendix_per_task.md` and the provider's list prices, rather than
from a guess.

    python scripts/run_budget.py
    python scripts/run_budget.py --budget 19.93     # what fits in what is left

Costs are list-price upper bounds: prompt caching, which the archive shows some
runs benefiting from and others not, only makes them smaller.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import import_study_runs as I  # noqa: E402

ARCHIVE = pathlib.Path("docs/exports")

#: USD per million tokens, from `docs/exports/csv/openrouter_models.csv`.
PRICES = {
    "qwen3.6-flash": (0.25, 1.50),
    "minimax-m3": (0.30, 1.20),
    "kimi-k2.6": (0.7448, 4.655),
    "deepseek-v4-pro": (0.435, 0.87),
    "gpt-5-mini": (0.25, 2.00),
}

#: Archive run -> the configuration whose per-task cost it measures.
MEASURED = {
    "S1 (descriptive)": "Run 1: qwen3.6-flash S1 descriptive RefactorBench",
    "S1 (base, +LSP)": "qwen3.6-flash S1 base+LSP RefactorBench",
    "S2 (naive chunking)": "Run 3: qwen3.6-flash S2-naive desc",
}


def _num(value: str | None) -> float | None:
    text = (value or "").strip().replace(",", "").replace("'", "")
    if not text or text in "-—":
        return None
    match = re.match(r"^([\d.]+)\s*([kKmM]?)$", text)
    return float(match.group(1)) * {"k": 1e3, "m": 1e6, "": 1}[match.group(2).lower()] if match else None


def per_task_tokens(rows: list[dict]) -> tuple[float, float, int] | None:
    columns = list(rows[0].keys()) if rows else []
    ins = [c for c in columns if re.fullmatch(r"(?i)input(_?tokens)?", c)]
    outs = [c for c in columns if re.fullmatch(r"(?i)output(_?tokens)?", c)]
    if not ins or not outs:
        return None
    i = [v for v in (_num(r.get(ins[0])) for r in rows) if v is not None]
    o = [v for v in (_num(r.get(outs[0])) for r in rows) if v is not None]
    if not i:
        return None
    return sum(i) / len(i), (sum(o) / len(o) if o else 0.0), len(i)


def cost(tokens: tuple[float, float, int], model: str = "qwen3.6-flash") -> float:
    prompt, completion = PRICES[model]
    return tokens[0] * prompt / 1e6 + tokens[1] * completion / 1e6


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=pathlib.Path, default=ARCHIVE)
    ap.add_argument("--budget", type=float, help="flag plans that fit under this many USD")
    ap.add_argument("--repeats", type=int, default=5,
                    help="target runs per configuration, counting the one already done")
    args = ap.parse_args()

    runs = {r["title"]: r for r in I.parse_appendix(args.archive / "appendix_per_task.md")}
    measured = {}
    print("Measured per-task cost on qwen3.6-flash "
          f"(${PRICES['qwen3.6-flash'][0]}/M in, ${PRICES['qwen3.6-flash'][1]}/M out)\n")
    print(f"  {'configuration':22s} {'in/task':>10s} {'out/task':>9s} {'$/task':>8s}")
    for label, title in MEASURED.items():
        if title not in runs:
            continue
        tokens = per_task_tokens(runs[title]["rows"])
        if not tokens:
            continue
        measured[label] = cost(tokens)
        print(f"  {label:22s} {tokens[0]/1e3:9.1f}k {tokens[1]/1e3:8.1f}k "
              f"{measured[label]:8.3f}")

    s1 = measured.get("S1 (descriptive)", 0.125)
    s2 = measured.get("S2 (naive chunking)", 0.137)
    # No qwen S3 run recorded tokens. The one multi-agent run that did
    # (deepseek, Run 13) spent 1.7x the input and 2.7x the output of its
    # single-agent counterpart; that ratio is applied here and is the least
    # certain number on the page.
    s3 = s1 * 1.7 + (s1 * 0.07) * 2.7

    extra = max(0, args.repeats - 1)
    plans = [
        ("S3 sub-agents, full 100 tasks, once (fixes the unmatched task set)", 1 * 100 * s3),
        (f"AST vs naive, descriptive only, {args.repeats} runs each", 2 * 100 * extra * s2),
        (f"AST vs naive, all 3 prompt modes, {args.repeats} runs each", 6 * 100 * extra * s2),
        (f"Full Table 1 ablation (12 configs), {args.repeats} runs each",
         6 * 100 * extra * s1 + 6 * 100 * extra * s2),
        (f"Cross-model Table 2 (4 models x S1+S2), {args.repeats} runs each", None),
    ]

    print(f"\nCampaign cost, at {args.repeats} runs per configuration "
          f"({extra} beyond the run already archived)\n")
    for label, total in plans:
        if total is None:
            continue
        fits = ""
        if args.budget is not None:
            fits = "  <- fits" if total <= args.budget else f"  ({total / args.budget:.0f}x over)"
        print(f"  {label:62s} ${total:8.2f}{fits}")

    # Table 2 spans four models at four different prices, so it is priced apart.
    cross = 0.0
    for model in ("qwen3.6-flash", "minimax-m3", "kimi-k2.6", "deepseek-v4-pro"):
        tokens = per_task_tokens(runs["Run 1: qwen3.6-flash S1 descriptive RefactorBench"]["rows"])
        cross += 2 * 100 * extra * cost(tokens, model)
    fits = ""
    if args.budget is not None:
        fits = "  <- fits" if cross <= args.budget else f"  ({cross / args.budget:.0f}x over)"
    print(f"  {f'Cross-model Table 2 (4 models x S1+S2), {args.repeats} runs each':62s} "
          f"${cross:8.2f}{fits}")

    if args.budget is not None:
        print(f"\nAgainst a ${args.budget:.2f} budget: "
              f"{int(args.budget // s2)} retrieval task-runs, or "
              f"{int(args.budget // s1)} baseline task-runs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
