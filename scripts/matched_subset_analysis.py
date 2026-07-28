#!/usr/bin/env python3
"""Compare configurations on the *same* tasks, not on whatever each one finished.

Two runs behind the study stopped early — `gpt-5-mini S1-eval` was rate-limited
after 33 of 177 SWE-Refactor tasks, and the `S3` sub-agent run crashed after 26 of
100 RefactorBench tasks. Reporting their pass rate over the tasks that *ran*
(85% and 77%) next to full-set rates invites a survivorship comparison: an easy
subset would inflate them, a hard subset would deflate them.

This module restricts every other configuration to exactly those task ids and
recomputes, which is the only comparison that means anything. `scripts/figures.py`
imports `compute_matched_subsets` to draw the figure; run this file directly to
refresh the machine-readable record:

    python scripts/matched_subset_analysis.py --archive docs/exports --out docs/figures
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from import_study_runs import (  # noqa: E402
    AST_OK, BUILD_OK, PASSED, REPO, TASK, TESTS_OK, parse_appendix, pick, truthy,
)


def verdict(row: dict, benchmark: str) -> bool | None:
    """The archive spells the verdict differently per run; derive it the same way
    the importer does — an explicit column if present, else the conjunction of the
    stages that were recorded."""
    v = truthy(pick(row, PASSED))
    if v is not None:
        return v
    if benchmark == "swe":
        ast, build = truthy(pick(row, AST_OK)), truthy(pick(row, BUILD_OK))
        return None if ast is None or build is None else (ast and build)
    return truthy(pick(row, TESTS_OK))


def swe_run(runs: dict, title: str) -> dict[str, bool]:
    out = {}
    for row in runs[title]["rows"]:
        uid, proj = pick(row, TASK), pick(row, REPO)
        if not uid or not proj or len(uid) < 40:   # some tables truncate the id
            continue
        v = verdict(row, "swe")
        if v is not None:
            out[f"{proj}/{uid}"] = v
    return out


def rate(d: dict[str, bool], keys=None) -> tuple[int, int]:
    sel = [v for k, v in d.items() if keys is None or k in keys]
    return sum(sel), len(sel)


def crash_prefix(rows: list[tuple[str, float, bool]], floor: float = 10.0) -> int:
    """Index where the harness died.

    After the crash every remaining task fails in a few seconds. Walk back from the
    end while rows are both fast and failing; what remains is what actually ran.
    """
    i = len(rows)
    while i > 0 and rows[i - 1][1] < floor and not rows[i - 1][2]:
        i -= 1
    return i


def _entry(label: str, results: dict[str, bool], subset: set[str]) -> dict:
    fp, ft = rate(results)                        # full run, as reported
    sp, st = rate(results, subset)                # restricted to the shared set
    return {
        "config": label,
        "full": {"passed": fp, "total": ft, "rate": round(100 * fp / ft, 1) if ft else None},
        "matched": {"passed": sp, "total": st, "rate": round(100 * sp / st, 1) if st else None},
    }


def compute_matched_subsets(archive: pathlib.Path) -> dict:
    """Both benchmarks, each configuration scored twice: as reported, and again on
    only the tasks the truncated run actually reached."""
    runs = {r["title"]: r for r in parse_appendix(archive / "appendix_per_task.md")}

    # qwen3.6-flash S1: its per-task verdict file has truncated ids, but the run
    # log (swe_compound_qwen36flash_s1.csv) keeps *full* task ids and carries the
    # verdict in `status` (success/failed/timed_out). Its keys align with the
    # others, so qwen joins the matched comparison directly.
    qwen = {}
    with (archive / "csv" / "swe_compound_qwen36flash_s1.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            proj, tid = r["project_or_repo"].strip(), r["task_id"].strip()
            if proj and len(tid) >= 40:
                qwen[f"{proj}/{tid}"] = r["status"].strip().lower() == "success"

    matchable = [
        ("gpt-5-mini\nS1-eval", swe_run(runs, "Run 17: gpt-5-mini S1-eval SWE-Refactor")),
        ("gpt-5-mini\nS1", swe_run(runs, "Run 16: gpt-5-mini S1 default SWE-Refactor")),
        ("minimax-m3\nS1", swe_run(runs, "Run 14: minimax-m3 S1 SWE-Refactor")),
        ("qwen3.6-flash\nS1", qwen),
    ]
    # A matched comparison must score every config on the *same* tasks, so
    # restrict to the tasks all of them ran; otherwise each bar's rate is over a
    # different set and n varies per bar.
    subset = set.intersection(*(set(d) for _label, d in matchable))
    swe = [_entry(label, results, subset) for label, results in matchable]

    # --- RefactorBench: the S3 sub-agent run crashed partway through -----------
    crash_csv = archive / "csv" / "s3_copilot_subagent_descriptive_refbench - crash.csv"
    with crash_csv.open(encoding="utf-8") as fh:
        s3_rows = [(r["task_id"], float(r["duration_seconds"] or 0),
                    r["passed"].strip().lower() == "true") for r in csv.DictReader(fh)]
    ran = crash_prefix(s3_rows)
    s3_subset = {t for t, _, _ in s3_rows[:ran]}

    def refbench_run(title: str) -> dict[str, bool]:
        out = {}
        for row in runs[title]["rows"]:
            name = pick(row, TASK)
            v = verdict(row, "refbench")
            if name and v is not None:
                out[name] = v
        return out

    def refbench_csv(path: pathlib.Path) -> dict[str, bool]:
        """Some archive CSVs end with a `TOTAL` summary row; a non-boolean verdict
        is the tell (that row is the source of the long-standing 101-of-100 count)."""
        with path.open(encoding="utf-8") as fh:
            rows = {r["task_id"]: truthy(r["passed"]) for r in csv.DictReader(fh)}
        return {k: v for k, v in rows.items() if v is not None}

    rb_configs = [
        ("S3 sub-agents\n(crashed)", {t: p for t, _, p in s3_rows[:ran]}),
        ("S1 baseline", refbench_run("Run 1: qwen3.6-flash S1 descriptive RefactorBench")),
        ("S2 AST retrieval", refbench_csv(archive / "csv" / "s2_rag_descriptive_refbench.csv")),
    ]
    return {
        "swe": swe,
        "refbench": [_entry(label, results, s3_subset) for label, results in rb_configs],
        "sweSharedTasks": len(subset),
        "s3TasksExecuted": ran,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()

    report = compute_matched_subsets(args.archive)
    print(f"S3 sub-agent run executed {report['s3TasksExecuted']} tasks before crashing; "
          f"{report['sweSharedTasks']} SWE tasks are shared by every configuration\n")
    print(json.dumps(report, indent=2))

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "matched_subset.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out / 'matched_subset.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
