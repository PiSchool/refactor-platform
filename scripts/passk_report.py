#!/usr/bin/env python3
"""Turn a repeated-run campaign into a report a team can read.

`repeat_stats.py` prints the statistics; this writes the same evidence as a
markdown page, including the one thing a rate cannot show — which individual
tasks changed verdict between identical runs. That per-task table is what
answers "is pass@k worth reporting at all here?": if nothing flips, repeats are
wasted budget, and saying so is a finding.

    python scripts/passk_report.py --campaign docs/exports/passk_probe.json --out report.md
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from repeat_stats import mean_interval, pass_at_k  # noqa: E402


def merge(runs: list[dict]) -> dict[tuple[str, int], dict]:
    """Batches are not repeats; pool them back into one entry per repeat."""
    out: dict[tuple[str, int], dict] = {}
    for r in runs:
        key = (r["setup"], r["repeat"])
        e = out.setdefault(key, {"setup": r["setup"], "repeat": r["repeat"],
                                 "passed": 0, "total": 0, "perTask": {}, "seconds": []})
        e["passed"] += r["passed"]
        e["total"] += r["total"]
        e["perTask"].update(r["perTask"])
        e["seconds"].extend(r.get("secondsPerTask") or [])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--campaign", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()

    runs = json.loads(args.campaign.read_text(encoding="utf-8")).get("runs", [])
    if not runs:
        raise SystemExit("no runs recorded yet")
    merged = merge(runs)

    by_setup: dict[str, list[dict]] = {}
    for e in merged.values():
        by_setup.setdefault(e["setup"], []).append(e)
    for entries in by_setup.values():
        entries.sort(key=lambda x: x["repeat"])

    model = runs[0].get("model", "?")
    tasks = sorted({t for e in merged.values() for t in e["perTask"]})
    lines = [
        "# Pass@k probe — is repeating runs worth the budget?",
        "",
        f"Model `{model}` (free tier), GitHub Copilot CLI, RefactorBench descriptive prompts.",
        "",
        "Tasks were **not** chosen at random. They are tasks the published study found "
        "hard: ones whose verdict changed between execution regimes, plus ones that "
        "failed in every regime. A task that always passes or always fails tells you "
        "nothing about run-to-run variation, so those would waste the measurement.",
        "",
        "## Per-setup results",
        "",
        "| Setup | Runs | Per-run rates | Mean | SD | 95% CI | pass@1 | pass@k | Flipped |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    complete, flips_total = [], 0
    for setup, entries in sorted(by_setup.items()):
        rates = [round(100 * e["passed"] / e["total"], 1) for e in entries if e["total"]]
        if not rates:
            continue
        mean, sd, lo, hi = mean_interval(rates)
        pk = pass_at_k([e["perTask"] for e in entries])
        flips_total += pk.get("flipped", 0)
        if len(rates) >= 2:
            complete.append(setup)
        lines.append(
            f"| `{setup}` | {len(rates)} | {rates} | {mean:.1f}% | {sd:.2f} | "
            f"[{lo:.1f}, {hi:.1f}] | {pk.get('pass@1','-')}% | "
            f"{pk.get('pass@k','-')}% | {pk.get('flipped','-')}/{pk.get('tasks','-')} |")

    lines += ["", "## Which tasks actually changed verdict", "",
              "`.` = failed, `P` = passed, one column per repeat. A row that is not "
              "all-`.` or all-`P` is a task where an identical configuration "
              "disagreed with itself.", ""]
    header = "| Task | " + " | ".join(f"`{s}`" for s in sorted(by_setup)) + " |"
    lines += [header, "|" + "---|" * (len(by_setup) + 1)]
    for task in tasks:
        cells = []
        for setup in sorted(by_setup):
            seq = "".join("P" if e["perTask"].get(task) else "." for e in by_setup[setup])
            unstable = len(set(seq)) > 1
            cells.append(f"**{seq}**" if unstable else seq)
        lines.append(f"| `{task.split('/')[-1].removesuffix('#descriptive')}` | "
                     + " | ".join(cells) + " |")

    every = [e for entries in by_setup.values() for e in entries]
    secs = [s for e in every for s in e["seconds"]]
    lines += ["", "## Verdict on pass@k", ""]
    if flips_total == 0:
        lines += ["**No task changed verdict across repeats.** On this benchmark and "
                  "model the agent is effectively deterministic, so pass@k equals "
                  "pass@1 and repeated runs buy nothing. That is a reportable finding: "
                  "it says the single-run numbers in the paper are not luck, and it "
                  "means budget is better spent on more tasks than on more repeats."]
    else:
        lines += [f"**{flips_total} task-verdict flips** across repeats. Repeats do "
                  f"carry information here: pass@k exceeds pass@1, so a single run "
                  f"understates what the configuration can do, and the paper's "
                  f"single-run rates carry run-to-run uncertainty on top of the "
                  f"task-sampling uncertainty already reported."]
    if secs:
        lines += ["", f"Cost: {len(secs)} task-runs, median "
                      f"{statistics.median(secs):.0f}s each, "
                      f"{sum(secs)/3600:.1f} h of compute. Model spend: $0 (free tier)."]
    if len(complete) < len(by_setup):
        pending = sorted(set(by_setup) - set(complete))
        lines += ["", f"> Still running: {', '.join('`'+s+'`' for s in pending)}. "
                      "Setups are completed one at a time, so every setup shown above "
                      "with more than one run has its full set of repeats."]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    print("\n".join(lines[:20]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
