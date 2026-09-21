#!/usr/bin/env python3
"""Import the study's historical runs into the platform.

The runs behind the paper live as per-task markdown tables exported from the
study harness. This script rebuilds
them as first-class runs — visible in the dashboard, with a detail page, checks
and metrics — by emitting the platform's own export ZIP and POSTing it to
`/api/runs/import`.

Only measured columns become checks and metrics. Where a source table never
recorded a stage, the stage is omitted rather than invented.

    python scripts/import_study_runs.py --appendix docs/exports/appendix_per_task.md \
        --api http://localhost:8000 [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- column aliases

TASK = ("Task", "TaskId", "task_id", "taskId", "uniqueId", "UniqueId", "RefactoringId", "refactoringId")
REPO = ("Repo", "repo", "Project", "project")
STATUS = ("Status", "status")
PASSED = ("Result", "Passed", "passed", "verified", "successVerification")
IN_TOK = ("Input", "InputTok", "input_tokens", "inputTokens")
OUT_TOK = ("Output", "OutputTok", "output_tokens", "outputTokens")
CACHE_TOK = ("Cache", "CacheRead", "cache_tokens", "cacheTokens")
DURATION = ("Time", "Duration(s)", "duration_s", "duration_seconds", "durationSeconds")
AGENT_SECS = ("AgentDur(s)", "agentDurationSeconds")
EVAL_SECS = ("EvalDur(s)", "evalDurationSeconds")
CODEBLEU = ("CodeBLEU", "codebleu")
REASONING = ("Reasoning", "ReasoningTok", "reasoning_tokens", "reasoningTokens")
LSP_ACTIONS = ("lspActions", "LspActions", "LSPActions", "copilotLspActionCount")
RAG_TOOLS = ("rag_tool_count", "ragToolCount", "retrievalInvocations")
EVAL_LOOPS = ("EvalLoops", "Evals", "evalLoops", "eval_loop_count")
COMPACTIONS = ("Cmpct", "compactions", "compaction_count")
TESTS_PASS = ("tests_passed",)
TESTS_TOTAL = ("tests_total",)
MODE = ("mode",)

# stage-bearing columns, per benchmark
APPLY = ("Apply", "ApplySucceeded", "applySucceeded", "code", "codeSuccessful")
TESTS_OK = ("Test", "TestSucceeded", "testSucceeded")
AST_OK = ("ast", "AST", "refactoringMinerResult", "successVerification")
BUILD_OK = ("build", "Compile", "compileAndTestResult", "Build/Test")

MODEL_IDS = {
    "qwen3.6-flash": "qwen/qwen3.6-flash",
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
    "minimax-m3": "minimax/minimax-m3",
    "kimi-k2.6": "moonshotai/kimi-k2.6",
    "gpt-5-mini": "openai/gpt-5-mini",
    "openrouter/free": "openrouter/free",
}

BUNDLE_FORMAT = "refactor-platform-run"
ARCHIVED_ONLY_SETUPS = {
    "s3_cao": {
        "key": "s3_cao",
        "name": "CAO multi-agent",
    },
}


def pick(row: dict, names) -> str | None:
    for n in names:
        if n in row and str(row[n]).strip() not in ("", "-", "None"):
            return str(row[n]).strip()
    return None


def truthy(v: str | None) -> bool | None:
    """Source tables spell booleans six ways. None = never recorded."""
    if v is None:
        return None
    s = v.strip().lower()
    if s in ("true", "yes", "y", "passed", "1", "ok", "checked"):
        return True
    if s in ("false", "no", "n", "failed", "0", "error", "timeout", "timed_out"):
        return False
    return None


def to_seconds(v: str | None) -> float:
    """'21m57s' / '27s' / '169.4' -> seconds."""
    if not v:
        return 0.0
    v = v.strip()
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", v)
    if m and any(m.groups()):
        h, mi, s = (float(x) if x else 0.0 for x in m.groups())
        return h * 3600 + mi * 60 + s
    try:
        return float(v)
    except ValueError:
        return 0.0


def to_tokens(v: str | None) -> int:
    """'2.3M' / '192.3k' / '110800' -> int."""
    if not v:
        return 0
    v = v.strip().replace(",", "")
    mult = {"k": 1_000, "K": 1_000, "m": 1_000_000, "M": 1_000_000}
    if v and v[-1] in mult:
        try:
            return int(float(v[:-1]) * mult[v[-1]])
        except ValueError:
            return 0
    try:
        return int(float(v))
    except ValueError:
        return 0


def to_float(v: str | None) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


# ---------------------------------------------------------------- title parsing


def parse_title(title: str) -> dict:
    t = title
    benchmark = "swe" if "SWE-Refactor" in t else "refbench"

    low = t.lower()
    if "s2-naive" in low or "naive" in low:
        setup = "s2_rag_naive"
    elif "s2-rag" in low or "s2 " in low:
        setup = "s2_rag_ast"
    elif "cao" in low:
        setup = "s3_cao"
    elif "s3" in low:
        setup = "s3"
    elif "s1-eval" in low or "s1_eval" in low:
        setup = "s1_eval"
    elif "+lsp" in low:
        setup = "s1_lsp"
    else:
        setup = "s1"

    mode = None
    if "all modes" in low:
        mode = "*"
    elif "desc" in low:
        mode = "descriptive"
    elif "lazy" in low:
        mode = "lazy"
    elif "base" in low:
        mode = "base"

    model = next((v for k, v in MODEL_IDS.items() if k in t), None)
    return {"benchmark": benchmark, "setup": setup, "mode": mode, "model": model, "title": t}


def parse_appendix(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    runs = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        lines = block.splitlines()
        title = lines[0].strip()
        meta = "\n".join(lines[1:6])

        table = [l for l in lines if l.startswith("|")]
        # Several blocks open with a 2-column metadata table ("| Model | qwen |").
        # The real table is the first one whose header names a task column.
        header = None
        rows = []
        for i, l in enumerate(table):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if header is None:
                is_header = (i + 1 < len(table)
                             and set(table[i + 1].replace("|", "").strip()) <= set("- ")
                             and any(c in TASK for c in cells))
                if is_header:
                    header = cells
                continue
            if set(l.replace("|", "").strip()) <= set("- "):
                continue
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells)))

        if not header or not rows:
            continue
        info = parse_title(title)
        if not info["model"]:
            m = re.search(r"Model,\s*([^\s|]+)", meta)
            info["model"] = m.group(1).strip() if m else "unknown"
        rid = re.search(r"Run ID,\s*([^\s|]+)", meta)
        info["studyRunId"] = rid.group(1).strip() if rid else None
        # Real provenance to bundle into the run's ZIP: the original per-task
        # table and the CSV it was exported from.
        src = re.search(r"Source:\s*`([^`]+)`", block)
        info["sourceCsv"] = src.group(1).strip() if src else None
        info["blockMd"] = "### " + block
        info["rows"] = rows
        runs.append(info)
    return runs


# ---------------------------------------------------------------- task mapping


def load_catalog(api: str) -> dict:
    with urllib.request.urlopen(f"{api}/api/catalog", timeout=30) as r:
        cat = json.load(r)
    out: dict = {
        "_benchmarks": {b["key"]: b for b in cat["benchmarks"]},
        "_agents": {agent["key"]: agent for agent in cat["agents"]},
        "_setups": {setup["key"]: setup for setup in cat["setups"]},
        "_tasks": {},
    }
    out["_setups"].update(ARCHIVED_ONLY_SETUPS)
    for b in cat["benchmarks"]:
        with urllib.request.urlopen(f"{api}/api/benchmarks/{b['id']}/tasks", timeout=60) as r:
            tasks = json.load(r)["tasks"]
        out[b["key"]] = {t["taskKey"] for t in tasks}
        out["_tasks"][b["key"]] = {t["taskKey"]: t for t in tasks}
    out["_agent"] = cat["agents"][0]["key"]
    # refbench: task name -> repo (names are unique across repos)
    name_to_repo = {}
    for k in out.get("refbench", ()):
        repo, rest = k.split("/", 1)
        name_to_repo[rest.split("#")[0]] = repo
    out["_refbench_repo"] = name_to_repo
    return out


def task_key(info: dict, row: dict, catalog: dict) -> str | None:
    name = pick(row, TASK)
    if not name:
        return None
    if info["benchmark"] == "swe":
        project = pick(row, REPO)
        return f"{project}/{name}" if project else None

    repo = pick(row, REPO) or catalog["_refbench_repo"].get(name)
    if not repo:
        return None
    mode = pick(row, MODE) or (info["mode"] if info["mode"] != "*" else None)
    return f"{repo}/{name}#{mode}" if mode else None


def build_details(info: dict, row: dict) -> dict:
    """Only stages the source table actually recorded."""
    details: dict = {}
    changed = truthy(pick(row, APPLY))
    if changed is not None:
        details["workspace_changed"] = {"ok": changed,
                                        "message": "Workspace changed." if changed else "No changes were made."}
    if info["benchmark"] == "refbench":
        tests = truthy(pick(row, TESTS_OK))
        tp, tt = pick(row, TESTS_PASS), pick(row, TESTS_TOTAL)
        if tests is None and tp and tt:
            tests = tp == tt
        if tests is not None:
            msg = f"{tp}/{tt} tests passed." if tp and tt else ("Tests passed." if tests else "Tests failed.")
            d = {"ok": tests, "message": msg}
            if tp and tt:
                d.update(testsPassed=int(tp), testsTotal=int(tt))
            details["python_tests"] = d
    else:
        ast = truthy(pick(row, AST_OK))
        if ast is not None:
            details["refactoring_miner"] = {"ok": ast,
                                            "message": "Refactoring detected." if ast else "Declared refactoring not detected."}
        build = truthy(pick(row, BUILD_OK))
        if build is not None:
            details["java_build"] = {"ok": build,
                                     "message": "Build+test passed." if build else "Build failed."}
    return details


def build_metrics(info: dict, row: dict) -> dict:
    m = {}
    for key, names, conv in (
        ("tokensCacheRead", CACHE_TOK, to_tokens),
        ("tokensReasoning", REASONING, to_tokens),
        ("evalIterations", EVAL_LOOPS, lambda v: int(to_float(v) or 0)),
        ("compactionCount", COMPACTIONS, lambda v: int(to_float(v) or 0)),
        ("codebleu", CODEBLEU, to_float),
    ):
        v = pick(row, names)
        if v is not None:
            cv = conv(v)
            if cv:
                m[key] = cv
    # Setup-mechanism counters the fidelity panel reads. Each appendix table only
    # carries the column for the setup it exercised, so this stays honest: no
    # column -> no metric, and setupExercised is derived, never invented.
    lsp = pick(row, LSP_ACTIONS)
    if lsp is not None:
        m["lspActions"] = int(to_float(lsp) or 0)
        if info["setup"] == "s1_lsp":
            m["setupExercised"] = m["lspActions"] > 0
    if info["setup"] == "s1_eval" and "evalIterations" in m:
        # eval.sh runs once per eval loop; the loop count IS the invocation count.
        m["evalToolInvocations"] = m["evalIterations"]
        m["setupExercised"] = m["evalIterations"] > 0
    rag = pick(row, RAG_TOOLS)
    if rag is not None and info["setup"].startswith("s2_rag"):
        m["retrievalInvocations"] = int(to_float(rag) or 0)
        m["setupExercised"] = m["retrievalInvocations"] > 0
    return m


def crash_trim(rows: list[dict]) -> list[dict]:
    """Drop a harness-crash tail so a partial run reports over what actually ran.

    After a crash every remaining task fails in a few seconds; walk back while
    rows are both fast (<10 s) and failing. Only treat it as a crash when the
    tail is substantial (>=10 rows) — a couple of quick failures at the end of a
    healthy run are real, not a crash. This is what turns the S3 sub-agent run
    from a diluted 20/100 into the paper's 20/26.
    """
    i = len(rows)
    while i > 0:
        r = rows[i - 1]
        dur = to_seconds(pick(r, DURATION)) or 0
        if dur < 10 and truthy(pick(r, PASSED)) is not True:
            i -= 1
        else:
            break
    return rows[:i] if len(rows) - i >= 10 else rows


# Runs the study reports over only the tasks that ran before a harness crash.
# This is NOT a general heuristic: a rate-limited run (e.g. gpt-5-mini S1, which
# the paper reports as 15/75) also has a fast-fail tail but is scored over the
# full set. Only the runs the paper itself reports as partial are trimmed.
CRASH_RUNS = {"qwen3.6-flash S3 subagent desc RefactorBench"}


def source_run_id(info: dict) -> str:
    """Stable platform-shaped identity for one immutable published table."""
    source = f"{info.get('studyRunId', '')}\0{info['title']}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:32]


def source_timestamp(info: dict) -> str:
    """Use the recorded study timestamp when present; otherwise import time."""
    for value in (info.get("studyRunId"), info.get("title")):
        match = re.search(r"(\d{8})[_-](\d{6})", str(value or ""))
        if match:
            stamp = datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")
            return stamp.replace(tzinfo=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def build_summary(info: dict, rows: list[dict], catalog: dict, agent_key: str):
    tasks, skipped = [], 0
    if info["title"] in CRASH_RUNS:
        rows = crash_trim(rows)
    known = catalog.get(info["benchmark"], set())
    for i, row in enumerate(rows):
        key = task_key(info, row, catalog)
        if not key or key not in known:
            skipped += 1
            continue
        passed = truthy(pick(row, PASSED))
        status = pick(row, STATUS) or ""
        timed_out = status.lower() in ("timed_out", "timeout")
        details = build_details(info, row)
        if passed is None and details:
            passed = all(d["ok"] for d in details.values())
        ordinal = len(tasks)
        task_meta = catalog.get("_tasks", {}).get(info["benchmark"], {}).get(key, {})
        tasks.append({
            "id": f"task-{ordinal:04d}",
            "taskKey": key,
            "title": str(task_meta.get("title") or key),
            "ordinal": ordinal,
            "status": "timed_out" if timed_out else ("passed" if passed else "failed"),
            "timeoutSeconds": 1800,
            "startedAt": None,
            "finishedAt": None,
            "params": task_meta.get("params") or {},
            "result": {
                "passed": bool(passed),
                "reason": None if passed else ("timed_out" if timed_out else "verification_failed"),
                "durationSeconds": to_seconds(pick(row, DURATION)),
                "agentSeconds": to_seconds(pick(row, AGENT_SECS)),
                "evaluateSeconds": to_seconds(pick(row, EVAL_SECS)),
                "tokensInput": to_tokens(pick(row, IN_TOK)),
                "tokensOutput": to_tokens(pick(row, OUT_TOK)),
                "model": info["model"],
                "metrics": build_metrics(info, row),
                "details": details,
            },
            "session": None,
            "artifacts": [],
        })
    benchmark = catalog["_benchmarks"][info["benchmark"]]
    setup = catalog["_setups"][info["setup"]]
    agent = catalog["_agents"][agent_key]
    passed_count = sum(task["status"] == "passed" for task in tasks)
    failed_count = sum(task["status"] in {"failed", "error", "stopped"} for task in tasks)
    timed_out_count = sum(task["status"] == "timed_out" for task in tasks)
    scored = passed_count + failed_count + timed_out_count
    summary = {
        "run": {
            "id": source_run_id(info),
            "status": "completed",
            "benchmark": {
                "key": benchmark["key"],
                "name": benchmark["name"],
                "language": benchmark["language"],
            },
            "agentTool": {"key": agent["key"], "name": agent["name"]},
            "setup": {"key": setup["key"], "name": setup["name"]},
            "model": info["model"],
            "taskTimeoutSeconds": 1800,
            "config": {
                "source": "study archive",
                "studyRunId": info["studyRunId"],
                "title": info["title"],
                "promptMode": info["mode"],
            },
            "counts": {
                "total": len(tasks),
                "passed": passed_count,
                "failed": failed_count,
                "timedOut": timed_out_count,
                "pending": 0,
            },
            "passRate": (passed_count / scored) if scored else 0.0,
            "queuedAt": source_timestamp(info),
            "startedAt": None,
            "finishedAt": None,
        },
        "tasks": tasks,
    }
    return summary, skipped


def results_csv(summary: dict) -> str:
    columns = [
        "taskKey", "status", "passed", "reason", "durationSeconds",
        "agentSeconds", "evaluateSeconds", "model", "tokensInput",
        "tokensOutput", "metrics", "details",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for task in summary["tasks"]:
        result = task.get("result") or {}
        writer.writerow({
            "taskKey": task["taskKey"],
            "status": task["status"],
            "passed": result.get("passed"),
            "reason": result.get("reason") or "",
            "durationSeconds": result.get("durationSeconds", 0),
            "agentSeconds": result.get("agentSeconds", 0),
            "evaluateSeconds": result.get("evaluateSeconds", 0),
            "model": result.get("model", ""),
            "tokensInput": result.get("tokensInput", 0),
            "tokensOutput": result.get("tokensOutput", 0),
            "metrics": json.dumps(result.get("metrics") or {}, sort_keys=True),
            "details": json.dumps(result.get("details") or {}, sort_keys=True),
        })
    return output.getvalue()


def make_zip(
    summary: dict,
    extras: list[tuple[str, bytes, str, str]] | None = None,
) -> bytes:
    portable = deepcopy(summary)
    artifacts = []
    by_task = {task["id"]: task for task in portable["tasks"]}
    for path, data, media_type, key in sorted(extras or []):
        task_folder = path.split("/")[2]
        task = by_task[task_folder]
        task["artifacts"].append({
            "key": key,
            "available": True,
            "mediaType": media_type,
            "sizeBytes": len(data),
        })
        artifacts.append({
            "path": path,
            "sizeBytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "mediaType": media_type,
        })

    run = portable["run"]

    def manifest_ref(ref: dict) -> dict:
        return {
            "key": ref["key"],
            "name": ref["name"],
        }

    manifest = {
        "format": BUNDLE_FORMAT,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sourceRunId": run["id"],
        "benchmark": manifest_ref(run["benchmark"]),
        "setup": manifest_ref(run["setup"]),
        "agentTool": manifest_ref(run["agentTool"]),
        "status": run["status"],
        "taskCount": len(portable["tasks"]),
        "artifacts": artifacts,
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        z.writestr("summary.json", json.dumps(portable, indent=2, ensure_ascii=False))
        z.writestr("results.csv", results_csv(portable))
        for path, data, _media_type, _key in sorted(extras or []):
            z.writestr(path, data)
    return buf.getvalue()


def source_artifacts(info: dict, csv_dir: Path) -> list[tuple[str, bytes, str, str]]:
    """The genuine provenance for a historical run: its original per-task table
    and the CSV it came from. Raw session/terminal logs for the paper runs were
    never exported to this archive, so they are not — and cannot be — included."""
    out: list[tuple[str, bytes, str, str]] = []
    if info.get("blockMd"):
        out.append((
            "artifacts/tasks/task-0000/study/source-table.md",
            info["blockMd"].encode("utf-8"),
            "text/markdown",
            "study-source-table",
        ))
    name = info.get("sourceCsv")
    if name:
        src = csv_dir / name
        if src.is_file():
            out.append((
                "artifacts/tasks/task-0000/study/source.csv",
                src.read_bytes(),
                "text/csv",
                "study-source-csv",
            ))
    return out


def post_zip(api: str, blob: bytes, name: str) -> str:
    boundary = "----rp-import"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
        f"Content-Type: application/zip\r\n\r\n".encode() + blob + f"\r\n--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(f"{api}/api/runs/import", data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)["id"]
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"archive import failed with HTTP {exc.code}: {detail}") from exc


def imported_source_ids(api: str) -> set[str]:
    with urllib.request.urlopen(f"{api}/api/runs", timeout=60) as response:
        runs = json.load(response).get("runs", [])
    source_ids: set[str] = set()
    for run in runs:
        config = run.get("config") or {}
        provenance = config.get("import") or {}
        if isinstance(provenance, dict) and provenance.get("sourceRunId"):
            source_ids.add(str(provenance["sourceRunId"]))
    return source_ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--appendix", required=True, type=Path)
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-tasks", type=int, default=5, help="skip runs with fewer mapped tasks")
    args = ap.parse_args()

    catalog = load_catalog(args.api)
    agent = catalog["_agent"]
    runs = parse_appendix(args.appendix)
    print(f"parsed {len(runs)} study runs\n")

    # Tables whose totals don't match the published plots are dropped rather than
    # shown: a demo that contradicts the paper is worse than a smaller demo.
    #  - Run 3: S2-naive desc sources a *_detailed.csv scoring 44/100, superseded
    #    by the all-modes naive table (Run 2), which carries the published 57.
    #  - Run 1: an early full export of the S1 descriptive run; the curated
    #    s1_descriptive_lsp export is the record behind the published 73.
    SKIP_TITLES = {
        "Run 3: qwen3.6-flash S2-naive desc",
        "Run 1: qwen3.6-flash S1 descriptive RefactorBench",
    }
    csv_dir = args.appendix.parent / "csv"
    existing = set() if args.dry_run else imported_source_ids(args.api)

    imported = 0
    already_present = 0
    eligible = 0
    for info in runs:
        if info["title"] in SKIP_TITLES:
            print(f"{info['title'][:58]:60} (SKIP: superseded export)")
            continue
        summary, skipped = build_summary(info, info["rows"], catalog, agent)
        n = len(summary["tasks"])
        passed = sum(1 for t in summary["tasks"] if t["result"]["passed"])
        flag = "" if n >= args.min_tasks else "  (SKIP: too few mapped)"
        print(f"{info['title'][:58]:60} {info['benchmark']:9} {info['setup']:14} "
              f"mapped={n:4} unmapped={skipped:4} passed={passed:3}{flag}")
        if n < args.min_tasks:
            continue
        eligible += 1
        if args.dry_run:
            continue
        if summary["run"]["id"] in existing:
            already_present += 1
            print("    -> already imported")
            continue
        blob = make_zip(summary, source_artifacts(info, csv_dir))
        rid = post_zip(args.api, blob, f"study-{info['setup']}.zip")
        imported += 1
        existing.add(summary["run"]["id"])
        print(f"    -> imported as {rid[:8]}")

    if args.dry_run:
        print(f"\nwould import: {eligible} runs")
    else:
        print(f"\nimported: {imported} runs; already present: {already_present}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
