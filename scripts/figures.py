#!/usr/bin/env python3
"""Redraw every documentation figure from the per-task exports it claims to show.

Figures drift. A number gets edited in prose, a chart is re-exported from a
spreadsheet, and six months later the picture and the data disagree with nobody
noticing. So every figure here is computed from the CSVs shipped in
`docs/exports/`, and every headline number is cross-checked against the summary
row the study itself recorded. A mismatch raises instead of rendering.

Each figure is written twice — `<name>-light.png` and `<name>-dark.png` — so the
docs can serve the variant that matches the reader's GitHub theme.

    uv run --with matplotlib --no-project python scripts/figures.py
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from matched_subset_analysis import compute_matched_subsets  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
EXPORTS = REPO / "docs" / "exports"
FIGURES = REPO / "docs" / "figures"


@dataclass(frozen=True)
class Theme:
    """Colours for one GitHub appearance. Series hues are shared where possible
    so the two variants read as the same figure, not two different ones."""

    name: str
    bg: str
    fg: str
    muted: str
    grid: str
    baseline: str
    naive: str
    ast: str
    good: str
    reference: str


LIGHT = Theme("light", "#ffffff", "#1f2328", "#59636e", "#d1d9e0",
              "#8c959f", "#bc4c00", "#0969da", "#1a7f37", "#afb8c1")
DARK = Theme("dark", "#0d1117", "#e6edf3", "#9198a1", "#30363d",
             "#6e7681", "#db6d28", "#58a6ff", "#3fb950", "#484f58")
THEMES = (LIGHT, DARK)


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #

def _lines(name: str) -> list[str]:
    return (EXPORTS / "csv" / name).read_text(encoding="utf-8", errors="replace").splitlines()


def _rows(name: str) -> list[dict]:
    return list(csv.DictReader(_lines(name)))


def _table(name: str, header: str) -> list[dict]:
    """Summary exports open with human comment lines; parse from the real header."""
    lines = _lines(name)
    start = next(i for i, line in enumerate(lines) if line.startswith(f"{header},"))
    return [row for row in csv.DictReader(lines[start:]) if (row.get(header) or "").strip()]


def _true(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "success", "passed"}


def _report_summary(name: str) -> dict[str, str]:
    """Pull the `Summary` block out of a run-report CSV (`Passed`, `Total runs`…)."""
    lines = _lines(name)
    start = next(i for i, line in enumerate(lines) if line.startswith("Summary"))
    out = {}
    for line in lines[start + 1:start + 8]:
        cells = line.split(",")
        if len(cells) >= 2 and cells[0]:
            out[cells[0]] = cells[1]
    return out


def _passed_of_100(name: str) -> int:
    """Per-task RefactorBench CSV. A trailing `TOTAL` row is not a task."""
    return sum(1 for row in _rows(name)
               if (row.get("task_id") or row.get("taskId")) not in (None, "TOTAL")
               and _true(row.get("passed")))


def _mode_rates(name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in _rows(name):
        mode = (row.get("mode") or "").strip()
        if mode:
            counts[mode] = counts.get(mode, 0) + (1 if _true(row.get("status")) else 0)
    return counts


def refactorbench_by_prompt_mode() -> dict[str, dict[str, int]]:
    """qwen3.6-flash on the 100 RefactorBench tasks: prompt mode x setup."""
    naive = _mode_rates("s2_rag_naive_qwen36flash_all_modes_refbench.csv")
    data = {
        "S1 agent": {
            "lazy": int(_report_summary("s1_lazy_lsp_refbench.csv")["Passed"]),
            "base": _passed_of_100("s1_base_lsp_refbench.csv"),
            "descriptive": int(_report_summary("s1_descriptive_lsp_refbench.csv")["Passed"]),
        },
        "S2 line windows": {mode: naive[mode] for mode in ("lazy", "base", "descriptive")},
        "S2 AST chunks": {
            "lazy": _passed_of_100("s2_rag_lazy_refbench.csv"),
            "base": _passed_of_100("s2_rag_base_refbench.csv"),
            "descriptive": _passed_of_100("s2_rag_descriptive_refbench.csv"),
        },
    }
    published = next(row for row in _table("all_models_all_setups_summary.csv", "Model")
                     if row["Model"] == "qwen3.6-flash")
    expected = {
        ("S1 agent", "descriptive"): published["S1 desc"],
        ("S1 agent", "base"): published["S1 base"],
        ("S1 agent", "lazy"): published["S1 lazy"],
        ("S2 AST chunks", "descriptive"): published["S2-RAG desc"],
        ("S2 AST chunks", "base"): published["S2-RAG base"],
        ("S2 AST chunks", "lazy"): published["S2-RAG lazy"],
    }
    for (setup, mode), claim in expected.items():
        got = data[setup][mode]
        if f"{got}%" != claim:
            raise SystemExit(
                f"{setup}/{mode}: per-task files give {got}/100, the study summary claims {claim}")
    return data


def refactorbench_by_model() -> list[tuple[str, int, int]]:
    """Descriptive prompt, per model: S1 agent vs S2 AST retrieval."""
    s2 = {}
    for name in ("deepseek", "kimi", "minimax"):
        row = _table(f"{name}_s2_rag_descriptive_refbench.csv", "Model")[-1]
        s2[row["Model"]] = int(row["Passed"])
    s2["qwen/qwen3.6-flash"] = _passed_of_100("s2_rag_descriptive_refbench.csv")

    short = {"qwen/qwen3.6-flash": "qwen3.6-flash", "deepseek/deepseek-v4-pro": "deepseek-v4-pro",
             "minimax/minimax-m3": "minimax-m3", "moonshotai/kimi-k2.6": "kimi-k2.6"}
    summary = {row["Model"]: row for row in _table("all_models_all_setups_summary.csv", "Model")}

    out = []
    for full, label in short.items():
        published_s1, published_s2 = summary[label]["S1 desc"], summary[label]["S2-RAG desc"]
        if f"{s2[full]}%" != published_s2:
            raise SystemExit(f"{label}: S2 files give {s2[full]}/100, summary claims {published_s2}")
        out.append((label, int(published_s1.rstrip("%")), s2[full]))
    return sorted(out, key=lambda item: item[2], reverse=True)


def swe_verification_funnel() -> tuple[list[tuple[str, int]], int, dict[str, tuple[int, int]]]:
    """The compound Java set, stage by stage, plus the per-refactoring breakdown."""
    rows = [r for r in _rows("swe_compound_qwen36flash_s1_FINAL.csv") if r["#"] not in ("", "TOTAL")]
    total = len(rows)
    stages = [
        ("Produced code", sum(1 for r in rows if _true(r["codeSuccessful"]))),
        ("Refactoring detected", sum(1 for r in rows if _true(r["refactoringMinerResult"]))),
        ("Build + tests green", sum(1 for r in rows if _true(r["compileAndTestResult"]))),
        ("Task passed", sum(1 for r in rows if _true(r["successVerification"]))),
    ]
    by_type: dict[str, tuple[int, int]] = {}
    for row in rows:
        kind = row["type"].strip() or "unlabelled"
        passed, seen = by_type.get(kind, (0, 0))
        by_type[kind] = (passed + int(_true(row["successVerification"])), seen + 1)

    recorded = next(r for r in _rows("swe_compound_qwen36flash_s1_FINAL.csv") if r["#"] == "TOTAL")
    claimed = {
        "Produced code": recorded["codeSuccessful"],
        "Refactoring detected": recorded["refactoringMinerResult"],
        "Build + tests green": recorded["compileAndTestResult"],
        "Task passed": recorded["successVerification"],
    }
    for label, count in stages:
        if not claimed[label].strip().startswith(f"{count}/{total}"):
            raise SystemExit(f"{label}: recomputed {count}/{total}, TOTAL row says {claimed[label]}")
    return stages, total, by_type


def swe_by_model() -> list[tuple[str, int, int, bool]]:
    """`(label, passed, total, measured_here)` on the 177-task compound set."""
    out = []
    for row in _table("swe_refactor_all_models_summary.csv", "Model"):
        if "(" not in (row.get("Passed") or ""):
            continue
        passed, total = row["Passed"].split("(")[1].rstrip(")").split("/")
        paper = "paper" in row["Model"].lower()
        label = row["Model"].replace(" (paper)", "") + f"\n{row['Setup']}"
        out.append((label, int(passed), int(total), not paper))
    return out


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #

def chunking_frontier() -> list[tuple[str, float, float, float]]:
    """Chunking strategies as (label, purity, integrity, median unit lines).

    Produced by `scripts/chunking_ablation.py`, which measures both properties
    over the benchmark repositories without running a model.
    """
    source = EXPORTS / "chunking_ablation.json"
    if not source.is_file():
        raise SystemExit(f"{source} missing — run scripts/chunking_ablation.py --out docs/exports")
    pooled = json.loads(source.read_text(encoding="utf-8"))["pooled"]
    rows = [(name, values["purity"], values["integrity"], values["median_chunk_lines"])
            for name, values in pooled.items()]
    # Windows in ascending size, AST last so it draws on top.
    windows = sorted((r for r in rows if r[0] != "ast"), key=lambda r: r[3])
    return windows + [r for r in rows if r[0] == "ast"]


def draw_chunking_frontier(theme: Theme, data: list[tuple[str, float, float, float]]) -> pathlib.Path:
    windows = [row for row in data if row[0] != "ast"]
    ast = next(row for row in data if row[0] == "ast")

    fig, ax = _figure(theme, 7.6, 5.2)
    ax.plot([r[1] for r in windows], [r[2] for r in windows], "-o", color=theme.naive,
            linewidth=1.6, markersize=6, label="fixed line windows", zorder=2)
    # The large windows crowd into the top-left corner, so labels step outward
    # with size instead of sitting at a fixed offset and overlapping.
    for index, (label, purity, integ, _lines_) in enumerate(windows):
        reversed_rank = len(windows) - 1 - index
        ax.annotate(f"{label.replace('naive@', '')} lines" if index == 0 else
                    label.replace("naive@", ""),
                    (purity, integ), color=theme.muted, fontsize=9,
                    xytext=(10 + 7 * reversed_rank, -3), textcoords="offset points",
                    ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=theme.grid, linewidth=0.7,
                                    shrinkA=0, shrinkB=3) if reversed_rank else None)
    ax.scatter([ast[1]], [ast[2]], s=150, marker="*", color=theme.ast,
               label="AST chunks", zorder=3)
    ax.annotate("AST", (ast[1], ast[2]), color=theme.fg, fontsize=10, fontweight="bold",
                xytext=(-30, 6), textcoords="offset points")

    # The corner AST occupies and no window reaches.
    ax.axhline(ast[2], color=theme.ast, linewidth=0.9, linestyle=":", alpha=0.6)
    ax.axvline(ast[1], color=theme.ast, linewidth=0.9, linestyle=":", alpha=0.6)

    ax.set_xlabel("purity — how much of the retrieved unit is the definition (%)",
                  color=theme.muted, fontsize=10)
    ax.set_ylabel("integrity — definitions\nheld whole (%)", color=theme.muted, fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_ylim(55, 102)
    ax.grid(color=theme.grid, linewidth=0.8, alpha=0.7)
    legend = ax.legend(frameon=False, fontsize=10, loc="lower left", ncols=2,
                       bbox_to_anchor=(0, 1.015))
    for text in legend.get_texts():
        text.set_color(theme.fg)
    ax.set_title("RefactorBench corpus · a window trades one property for the other; "
                 "AST holds both", color=theme.muted, fontsize=10, loc="left", pad=30)
    return _save(fig, theme, "chunking-frontier")


def _figure(theme: Theme, width: float, height: float):
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(theme.bg)
    ax.set_facecolor(theme.bg)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(theme.grid)
    ax.tick_params(colors=theme.muted, labelsize=9.5, length=0)
    ax.set_axisbelow(True)
    return fig, ax


def _save(fig, theme: Theme, stem: str) -> pathlib.Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / f"{stem}-{theme.name}.png"
    fig.savefig(path, dpi=170, facecolor=theme.bg, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return path


def draw_prompt_modes(theme: Theme, data: dict[str, dict[str, int]]) -> pathlib.Path:
    modes = ["lazy", "base", "descriptive"]
    series = [("S1 agent", theme.baseline), ("S2 line windows", theme.naive), ("S2 AST chunks", theme.ast)]
    fig, ax = _figure(theme, 8.4, 4.3)
    width, positions = 0.26, range(len(modes))
    for index, (label, colour) in enumerate(series):
        offset = (index - 1) * width
        values = [data[label][mode] for mode in modes]
        bars = ax.bar([p + offset for p in positions], values, width, label=label, color=colour)
        for bar, value in zip(bars, values):
            ax.annotate(f"{value}", (bar.get_x() + bar.get_width() / 2, value), ha="center",
                        va="bottom", fontsize=9.5, color=theme.fg, xytext=(0, 2),
                        textcoords="offset points")
    ax.set_xticks(list(positions))
    ax.set_xticklabels(["lazy\n(what)", "base\n(what + where)", "descriptive\n(what + where + how)"],
                       color=theme.fg, fontsize=10)
    ax.set_ylabel("tasks passed, of 100", color=theme.muted, fontsize=10)
    ax.set_ylim(0, 100)
    ax.grid(axis="y", color=theme.grid, linewidth=0.8, alpha=0.7)
    legend = ax.legend(frameon=False, fontsize=10, loc="lower left", ncols=3,
                       bbox_to_anchor=(0, 1.015))
    for text in legend.get_texts():
        text.set_color(theme.fg)
    ax.set_title("RefactorBench · qwen3.6-flash · how the prompt and the retrieval strategy interact",
                 color=theme.muted, fontsize=10, loc="left", pad=34)
    return _save(fig, theme, "refactorbench-prompt-modes")


def draw_models(theme: Theme, data: list[tuple[str, int, int]]) -> pathlib.Path:
    fig, ax = _figure(theme, 8.4, 3.6)
    labels = [row[0] for row in data]
    positions = range(len(labels))
    height = 0.34
    for index, (_label, s1, s2) in enumerate(data):
        ax.barh(index + height / 2, s1, height, color=theme.baseline,
                label="S1 agent" if index == 0 else None)
        ax.barh(index - height / 2, s2, height, color=theme.ast,
                label="S2 AST retrieval" if index == 0 else None)
        for value, offset in ((s1, height / 2), (s2, -height / 2)):
            ax.annotate(f"{value}", (value, index + offset), va="center", ha="left",
                        fontsize=9.5, color=theme.fg, xytext=(4, 0), textcoords="offset points")
    ax.set_yticks(list(positions))
    ax.set_yticklabels(labels, color=theme.fg, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("tasks passed, of 100 (descriptive prompt)", color=theme.muted, fontsize=10)
    ax.grid(axis="x", color=theme.grid, linewidth=0.8, alpha=0.7)
    legend = ax.legend(frameon=False, fontsize=10, loc="lower left", ncols=2,
                       bbox_to_anchor=(0, 1.015))
    for text in legend.get_texts():
        text.set_color(theme.fg)
    return _save(fig, theme, "refactorbench-models")


def draw_funnel(theme: Theme, stages: list[tuple[str, int]], total: int) -> pathlib.Path:
    fig, ax = _figure(theme, 8.4, 3.4)
    labels = [label for label, _ in stages]
    values = [value for _, value in stages]
    colours = [theme.baseline, theme.baseline, theme.naive, theme.good]
    bars = ax.barh(range(len(values)), values, 0.62, color=colours)
    for index, (bar, value) in enumerate(zip(bars, values)):
        ax.annotate(f"{value} / {total}   {value / total * 100:.0f}%",
                    (value, index), va="center", ha="left", fontsize=10, color=theme.fg,
                    xytext=(6, 0), textcoords="offset points")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, color=theme.fg, fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlim(0, total * 1.16)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.set_title("SWE-Refactor · 177 compound Java tasks · qwen3.6-flash, single agent, single pass",
                 color=theme.muted, fontsize=10, loc="left", pad=12)
    return _save(fig, theme, "swe-verification-funnel")


def draw_swe_models(theme: Theme, data: list[tuple[str, int, int, bool]]) -> pathlib.Path:
    fig, ax = _figure(theme, 8.4, 3.9)
    data = sorted(data, key=lambda row: row[1] / row[2])
    labels = [row[0] for row in data]
    rates = [row[1] / row[2] * 100 for row in data]
    for index, (label, passed, total, measured) in enumerate(data):
        ax.barh(index, rates[index], 0.6,
                color=theme.ast if measured else theme.reference,
                hatch=None if measured else "///", edgecolor=theme.bg, linewidth=0)
        ax.annotate(f"{rates[index]:.0f}%  ({passed}/{total})", (rates[index], index), va="center",
                    ha="left", fontsize=9.5, color=theme.fg, xytext=(6, 0),
                    textcoords="offset points")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([label.replace("\n", " · ") for label in labels], color=theme.fg, fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_xlabel("tasks passed: refactoring detected and the project's own build and tests green",
                  color=theme.muted, fontsize=9.5)
    ax.grid(axis="x", color=theme.grid, linewidth=0.8, alpha=0.7)
    handles = [plt.Rectangle((0, 0), 1, 1, color=theme.ast),
               plt.Rectangle((0, 0), 1, 1, color=theme.reference, hatch="///")]
    legend = ax.legend(handles, ["measured on this platform", "published reference (GPT-4o-mini)"],
                       frameon=False, fontsize=9.5, loc="lower right")
    for text in legend.get_texts():
        text.set_color(theme.fg)
    return _save(fig, theme, "swe-models")


def draw_matched_subset(theme: Theme, report: list[dict], shared: int) -> pathlib.Path:
    fig, ax = _figure(theme, 8.4, 4.0)
    labels = [entry["config"] for entry in report]
    positions = range(len(labels))
    width = 0.36
    for index, entry in enumerate(report):
        full, matched = entry["full"], entry["matched"]
        ax.bar(index - width / 2, full["rate"], width, color=theme.baseline,
               label="as reported, on its own task set" if index == 0 else None)
        ax.bar(index + width / 2, matched["rate"], width, color=theme.ast,
               label=f"restricted to the {shared} shared tasks" if index == 0 else None)
        for value, offset, count in ((full["rate"], -width / 2, full["total"]),
                                     (matched["rate"], width / 2, matched["total"])):
            ax.annotate(f"{value:.0f}%\nn={count}", (index + offset, value), ha="center",
                        va="bottom", fontsize=9, color=theme.fg, xytext=(0, 2),
                        textcoords="offset points")
    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels, color=theme.fg, fontsize=10)
    ax.set_ylim(0, 105)
    ax.set_ylabel("verified pass rate", color=theme.muted, fontsize=10)
    ax.grid(axis="y", color=theme.grid, linewidth=0.8, alpha=0.7)
    legend = ax.legend(frameon=False, fontsize=9.5, loc="upper right")
    for text in legend.get_texts():
        text.set_color(theme.fg)
    ax.set_title("SWE-Refactor · a run that stopped early cannot be compared on its own survivors",
                 color=theme.muted, fontsize=10, loc="left", pad=12)
    return _save(fig, theme, "swe-matched-subset")


def main() -> int:
    global FIGURES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=FIGURES)
    FIGURES = parser.parse_args().out

    prompt_modes = refactorbench_by_prompt_mode()
    models = refactorbench_by_model()
    stages, total, by_type = swe_verification_funnel()
    swe_models = swe_by_model()
    frontier = chunking_frontier()
    matched = compute_matched_subsets(EXPORTS)

    written = []
    for theme in THEMES:
        written.append(draw_prompt_modes(theme, prompt_modes))
        written.append(draw_models(theme, models))
        written.append(draw_funnel(theme, stages, total))
        written.append(draw_swe_models(theme, swe_models))
        written.append(draw_matched_subset(theme, matched["swe"], matched["sweSharedTasks"]))
        written.append(draw_chunking_frontier(theme, frontier))

    print("RefactorBench, 100 tasks, qwen3.6-flash")
    for setup, values in prompt_modes.items():
        print(f"  {setup:16s} " + "  ".join(f"{mode} {values[mode]}" for mode in
                                            ("lazy", "base", "descriptive")))
    print("\nRefactorBench, descriptive prompt, per model (S1 / S2 AST)")
    for label, s1, s2 in models:
        print(f"  {label:18s} {s1} / {s2}")
    print(f"\nSWE-Refactor, {total} compound tasks")
    for label, value in stages:
        print(f"  {label:24s} {value}/{total} ({value / total * 100:.1f}%)")
    for kind, (passed, seen) in sorted(by_type.items(), key=lambda item: -item[1][1]):
        print(f"    {kind:26s} {passed}/{seen}")
    print(f"\nMatched subset: {matched['sweSharedTasks']} tasks shared by all SWE configurations")
    for entry in matched["swe"]:
        print(f"  {entry['config']:22s} full {entry['full']['passed']}/{entry['full']['total']}"
              f"   matched {entry['matched']['passed']}/{entry['matched']['total']}")

    print(f"\nwrote {len(written)} files to {FIGURES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
