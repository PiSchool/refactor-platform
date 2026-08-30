#!/usr/bin/env python3
"""Is AST chunking better because of *structure*, or just because of chunk size?

The study reports that AST-aware chunking beats fixed line windows by 25-30 pp,
and explains it structurally: windows "split code without regard to syntactic
boundaries". That explanation was asserted, never measured, and a fixed 80-line
window is one size out of many -- so the gap could equally be a granularity
artifact that a better-tuned window would close.

This measures the mechanism directly, over the real RefactorBench repositories,
with no model and no API calls:

* **Definition integrity** -- the share of function and class definitions that
  land wholly inside a single retrievable unit. A unit holding half a function is
  a unit that cannot answer "show me this function".
* A **window sweep**, so size is varied rather than assumed, including the window
  whose median unit length matches the AST chunker's. If AST still wins at
  matched size, size is not the explanation.

Definitions are enumerated from the file's own parse tree, independently of
either chunker, so neither strategy is scored against its own notion of a unit.

    python scripts/chunking_ablation.py --tasks-only     # gold-edited files
    python scripts/chunking_ablation.py --out docs/exports
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

from app.retrieval.chunking import chunk_repository  # noqa: E402

BENCH = ROOT / "plugins" / "benchmarks" / "refbench" / "data"
WINDOWS = [20, 40, 60, 80, 120, 160, 240]
GOLD_PATH = re.compile(r"""['"]((?:\.\./)+[^'"]+\.py)['"]""")


def definitions(path: pathlib.Path) -> list[tuple[int, int]]:
    """Every function and class definition in a file, as (start, end) lines."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, ValueError, OSError):
        return []
    return [(n.lineno, n.end_lineno or n.lineno) for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and n.end_lineno]


def gold_files(repo_dir: pathlib.Path) -> dict[str, set[str]]:
    """Repo-relative paths each task's verification test reads, per test file.

    The tests address the checkout from a working directory inside it, so a
    recorded path is resolved by dropping leading `../` segments until it names a
    file that exists. A path that never resolves is dropped rather than guessed.
    """
    out: dict[str, set[str]] = {}
    tests = BENCH / "tests" / repo_dir.name
    if not tests.is_dir():
        return out
    for test in sorted(tests.glob("*.py")):
        found = set()
        for raw in GOLD_PATH.findall(test.read_text(encoding="utf-8", errors="replace")):
            trimmed = raw
            while trimmed.startswith("../"):
                trimmed = trimmed[3:]
                if (repo_dir / trimmed).is_file():
                    found.add(trimmed)
                    break
        if found:
            out[test.stem] = found
    return out


def integrity(chunks, scope: set[str] | None,
              defs: dict[str, list[tuple[int, int]]]) -> tuple[int, int, list[float], list[int]]:
    """Two things at once, because either alone is gameable.

    *Integrity* — does some unit hold the whole definition? A 240-line window
    scores well here for a trivial reason: it swallows almost anything.

    *Purity* — of the tightest unit that does hold it, how much is the definition
    itself? This is what a big window gives away, and it is what the agent pays
    for: retrieving one definition drags in everything sharing its window, which
    both dilutes the embedding and consumes the context budget.

    A chunker has to win both. Returns intact, total, per-definition purities,
    and the payload (lines delivered) of each tightest containing unit.
    """
    spans: dict[str, list[tuple[int, int]]] = {}
    for c in chunks:
        if scope is None or c.path in scope:
            spans.setdefault(c.path, []).append((c.start_line, c.end_line))
    intact = total = 0
    purities: list[float] = []
    payloads: list[int] = []
    for rel, ranges in defs.items():
        if scope is not None and rel not in scope:
            continue
        covering = spans.get(rel, [])
        for start, end in ranges:
            total += 1
            holding = [(s, e) for s, e in covering if s <= start and e >= end]
            if not holding:
                continue
            intact += 1
            s, e = min(holding, key=lambda span: span[1] - span[0])
            unit = e - s + 1
            purities.append((end - start + 1) / unit)
            payloads.append(unit)
    return intact, total, purities, payloads


def measure(repo_dir: pathlib.Path, scope: set[str] | None) -> list[dict]:
    defs = {}
    for path in repo_dir.rglob("*.py"):
        rel = path.relative_to(repo_dir).as_posix()
        if scope is not None and rel not in scope:
            continue
        found = definitions(path)
        if found:
            defs[rel] = found

    rows = []
    strategies = [("ast", None)] + [("naive", w) for w in WINDOWS]
    for strategy, window in strategies:
        kwargs = {"window_lines": window, "overlap_lines": max(1, window // 4)} if window else {}
        chunks, report = chunk_repository(repo_dir, "python", strategy, **kwargs)
        scoped = [c for c in chunks if scope is None or c.path in scope]
        intact, total, purities, payloads = integrity(chunks, scope, defs)
        lengths = [c.end_line - c.start_line + 1 for c in scoped]
        rows.append({
            "strategy": strategy if window is None else f"naive@{window}",
            "window_lines": window,
            "chunks_in_scope": len(scoped),
            "chunks_total": report.chunks,
            "median_chunk_lines": statistics.median(lengths) if lengths else 0,
            "definitions": total,
            "definitions_intact": intact,
            "integrity": round(100 * intact / total, 1) if total else None,
            "purity": round(100 * statistics.mean(purities), 1) if purities else None,
            "median_payload_lines": statistics.median(payloads) if payloads else 0,
            "_purities": purities,
            "_payloads": payloads,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks-only", action="store_true",
                    help="score only the files the benchmark's own tests read")
    ap.add_argument("--repos", nargs="*", help="limit to these repositories")
    ap.add_argument("--out", type=pathlib.Path)
    args = ap.parse_args()

    repos = sorted(p for p in (BENCH / "repositories").iterdir() if p.is_dir())
    if args.repos:
        repos = [p for p in repos if p.name in args.repos]
    if not repos:
        raise SystemExit(f"no repositories under {BENCH / 'repositories'}")

    per_repo, totals = {}, {}
    for repo in repos:
        scope = None
        if args.tasks_only:
            scope = set().union(*gold_files(repo).values()) if gold_files(repo) else set()
            if not scope:
                print(f"{repo.name}: no resolvable gold files, skipped")
                continue
        rows = measure(repo, scope)
        per_repo[repo.name] = rows
        print(f"\n{repo.name}  ({rows[0]['definitions']} definitions"
              f"{f', {len(scope)} gold files' if scope is not None else ''})")
        print(f"  {'strategy':12s} {'units':>8s} {'median lines':>13s} "
              f"{'integrity':>10s} {'purity':>8s} {'payload':>8s}")
        for r in rows:
            print(f"  {r['strategy']:12s} {r['chunks_in_scope']:8d} "
                  f"{r['median_chunk_lines']:13.0f} {r['integrity']:9.1f}% "
                  f"{r['purity']:7.1f}% {r['median_payload_lines']:7.0f}")
        for r in rows:
            agg = totals.setdefault(r["strategy"], {"intact": 0, "definitions": 0, "units": 0,
                                                    "lines": [], "purities": [], "payloads": []})
            agg["intact"] += r["definitions_intact"]
            agg["definitions"] += r["definitions"]
            agg["units"] += r["chunks_in_scope"]
            agg["lines"].append(r["median_chunk_lines"])
            agg["purities"].extend(r.pop("_purities"))
            agg["payloads"].extend(r.pop("_payloads"))

    print(f"\n{'=' * 62}\nAll repositories pooled"
          f"{' (gold-edited files only)' if args.tasks_only else ''}")
    print(f"  {'strategy':12s} {'units':>9s} {'median lines':>13s} "
          f"{'integrity':>10s} {'purity':>8s} {'payload':>8s}")
    summary = {}
    for name, agg in totals.items():
        pct = 100 * agg["intact"] / agg["definitions"] if agg["definitions"] else 0
        median = statistics.median(agg["lines"]) if agg["lines"] else 0
        purity = 100 * statistics.mean(agg["purities"]) if agg["purities"] else 0
        payload = statistics.median(agg["payloads"]) if agg["payloads"] else 0
        summary[name] = {"units": agg["units"], "median_chunk_lines": median,
                         "definitions": agg["definitions"], "definitions_intact": agg["intact"],
                         "integrity": round(pct, 1), "purity": round(purity, 1),
                         "median_payload_lines": payload}
        print(f"  {name:12s} {agg['units']:9d} {median:13.0f} {pct:9.1f}% "
              f"{purity:7.1f}% {payload:7.0f}")

    others = [n for n in summary if n != "ast"]
    if "ast" in summary and others:
        a = summary["ast"]
        matched = min(others, key=lambda n: abs(summary[n]["median_chunk_lines"] - a["median_chunk_lines"]))
        best_int = max(others, key=lambda n: summary[n]["integrity"])
        print(f"\nAST: {a['integrity']}% integrity at {a['purity']}% purity, "
              f"{a['median_payload_lines']:.0f}-line payload.")
        print(f"  matched median size ({matched}): integrity "
              f"{a['integrity'] - summary[matched]['integrity']:+.1f} pp for AST")
        print(f"  best window integrity ({best_int}, {summary[best_int]['integrity']}%) buys it with "
              f"{summary[best_int]['purity']}% purity and a "
              f"{summary[best_int]['median_payload_lines']:.0f}-line payload "
              f"({summary[best_int]['median_payload_lines'] / max(a['median_payload_lines'], 1):.1f}x AST)")
        reach = [n for n in others if summary[n]["integrity"] >= a["integrity"]]
        if reach:
            cheapest = min(reach, key=lambda n: summary[n]["median_payload_lines"])
            print(f"  no window matches AST on both: {cheapest} is the cheapest to reach AST's "
                  f"integrity, at {summary[cheapest]['purity']}% purity vs AST's {a['purity']}%")
        else:
            print("  no window reaches AST's integrity at any size")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        path = args.out / ("chunking_ablation_gold.json" if args.tasks_only
                           else "chunking_ablation.json")
        path.write_text(json.dumps({"scope": "gold" if args.tasks_only else "repository",
                                    "pooled": summary, "per_repo": per_repo}, indent=2),
                        encoding="utf-8")
        print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
