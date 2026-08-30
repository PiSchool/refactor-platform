#!/usr/bin/env python3
"""Launch the same configuration N times, and record every per-task verdict.

Whether a result is stable across runs, or an artifact of one run, can only be
answered by executing the same configuration repeatedly over the same tasks and
keeping the per-task outcomes rather than just the rates —
`scripts/repeat_stats.py` scores what this produces.

Runs are launched one at a time and waited on, because the platform executes its
queue sequentially; launching them together would only confuse the dashboard.
Progress is checkpointed after every run, since a campaign of this length will
be interrupted at least once and must resume rather than restart.

    # measure one configuration before committing to the long run
    python scripts/repeat_campaign.py --repeats 1 --tasks 2 --setups s2_rag_ast

    # the campaign itself
    python scripts/repeat_campaign.py --repeats 5 --model stealth/ox-alpha
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.error
import urllib.request

#: A task's verdict is its status; only `passed` counts as a pass.
TERMINAL = ("passed", "failed", "error", "stopped", "timed_out")


def api(base: str, path: str, payload: dict | None = None, timeout: int = 60):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base}{path}", data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def catalog_ids(base: str, benchmark_key: str, agent_key: str) -> tuple[str, str]:
    catalog = api(base, "/api/catalog")
    bench = next(b for b in catalog["benchmarks"] if b["key"] == benchmark_key)
    agent = next(a for a in catalog["agents"] if a["key"] == agent_key)
    if not agent.get("available", True):
        raise SystemExit(f"agent {agent_key!r} is unavailable on this deployment")
    return bench["id"], agent["id"]


def task_keys(base: str, benchmark_id: str, mode: str, limit: int | None,
              repo: str | None) -> list[str]:
    payload = api(base, f"/api/benchmarks/{benchmark_id}/tasks")
    rows = payload if isinstance(payload, list) else payload.get("tasks", [])
    keys = sorted(r["taskKey"] for r in rows if r["taskKey"].endswith(f"#{mode}"))
    if repo:
        keys = [k for k in keys if k.startswith(f"{repo}/")]
    return keys[:limit] if limit else keys


def wait_for(base: str, run_id: str, poll: int = 30) -> dict:
    """Block until the run leaves a running state, reporting progress as it goes."""
    last = None
    while True:
        try:
            run = api(base, f"/api/runs/{run_id}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"    (poll failed: {exc}; retrying)", flush=True)
            time.sleep(poll)
            continue
        tasks = run.get("tasks", [])
        done = sum(1 for t in tasks if t.get("status") in TERMINAL)
        line = f"    {run.get('status', ''):10s} {done}/{len(tasks)}"
        if line != last:
            print(line, flush=True)
            last = line
        if run.get("status") in ("completed", "failed", "stopped", "cancelled"):
            return run
        time.sleep(poll)


def summarise(run: dict) -> dict:
    tasks = run.get("tasks", [])
    scored = [t for t in tasks if t.get("status") in TERMINAL]
    passed = sum(1 for t in scored if t.get("status") == "passed")
    return {
        "runId": run.get("id"),
        "status": run.get("status"),
        "passed": passed,
        "total": len(scored),
        "dispatched": len(tasks),
        "rate": round(100 * passed / len(scored), 1) if scored else None,
        "counts": run.get("counts"),
        "perTask": {t.get("taskKey"): (t.get("status") == "passed") for t in tasks},
        "secondsPerTask": _durations(tasks),
    }


def _durations(tasks: list[dict]) -> list[float]:
    out = []
    for task in tasks:
        started, finished = task.get("startedAt"), task.get("finishedAt")
        if not (started and finished):
            continue
        try:
            fmt = "%Y-%m-%dT%H:%M:%S"
            out.append(round(time.mktime(time.strptime(finished[:19], fmt))
                             - time.mktime(time.strptime(started[:19], fmt)), 1))
        except ValueError:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="http://127.0.0.1:8787")
    ap.add_argument("--benchmark", default="refbench")
    ap.add_argument("--agent", default="copilot")
    ap.add_argument("--model", default="stealth/ox-alpha")
    ap.add_argument("--mode", default="descriptive")
    ap.add_argument("--setups", nargs="+", default=["s2_rag_ast", "s2_rag_naive"])
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--tasks", type=int, default=None, help="limit, for a trial run")
    ap.add_argument("--repo", default=None, help="restrict to one repository")
    ap.add_argument("--task-keys", nargs="+", default=None,
                    help="exact task keys; overrides --repo/--tasks. Use to target the\n                         tasks a previous study found hard, where repeats are informative")
    ap.add_argument("--timeout", type=int, default=3600, help="per-task seconds")
    # One long run loses everything when the stack restarts under it, and a
    # single errored task aborts the rest. Batching bounds both: a lost batch
    # costs minutes, and the checkpoint resumes at the batch that failed.
    ap.add_argument("--batch", type=int, default=10, help="tasks per run")
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path("docs/exports/repeat_campaign.json"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bench_id, tool_id = catalog_ids(args.base, args.benchmark, args.agent)
    keys = args.task_keys or task_keys(args.base, bench_id, args.mode, args.tasks, args.repo)
    if not keys:
        raise SystemExit(f"no {args.mode} tasks matched")
    planned = args.repeats * len(args.setups) * len(keys)
    print(f"{args.benchmark}/{args.mode}  tasks={len(keys)}  model={args.model}")
    print(f"plan: {args.repeats} repeats x {len(args.setups)} setups x {len(keys)} tasks "
          f"= {planned} task-runs")
    if args.dry_run:
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    record = json.loads(args.out.read_text()) if args.out.is_file() else {"runs": []}
    done = {(r["setup"], r["repeat"], r.get("batch", 0)) for r in record["runs"]}

    batches = [keys[i:i + args.batch] for i in range(0, len(keys), args.batch)]
    # Setup-major on purpose: pass@k needs every repeat of a setup, so finishing
    # one setup's k runs before starting the next means an interrupted campaign
    # still reports a complete pass@k for the setups it reached, instead of k=1
    # for all of them.
    for setup in args.setups:
        for repeat in range(1, args.repeats + 1):
            for index, batch in enumerate(batches):
                if (setup, repeat, index) in done:
                    print(f"[{setup} #{repeat} batch {index + 1}/{len(batches)}] recorded, skipping")
                    continue
                print(f"[{setup} #{repeat} batch {index + 1}/{len(batches)}] "
                      f"launching {len(batch)} task(s)")
                started = time.time()
                created = api(args.base, "/api/runs", {
                    "benchmarkId": bench_id, "setupId": setup, "agentToolId": tool_id,
                    "model": args.model, "taskKeys": batch,
                    "taskTimeoutSeconds": args.timeout,
                })
                entry = {"setup": setup, "repeat": repeat, "batch": index,
                         "model": args.model, "wallSeconds": None,
                         **summarise(wait_for(args.base, created["id"]))}
                entry["wallSeconds"] = round(time.time() - started, 1)
                record["runs"].append(entry)
                args.out.write_text(json.dumps(record, indent=2), encoding="utf-8")
                per = entry["secondsPerTask"]
                median = sorted(per)[len(per) // 2] if per else None
                print(f"[{setup} #{repeat} batch {index + 1}/{len(batches)}] "
                      f"{entry['passed']}/{entry['total']} = {entry['rate']}%  "
                      f"wall {entry['wallSeconds']:.0f}s  median/task "
                      f"{f'{median:.0f}s' if median else '-'}  -> {args.out}")

    print("\nsummary (batches pooled within each repeat)")
    for setup in args.setups:
        per_repeat: dict[int, list[dict]] = {}
        for r in record["runs"]:
            if r["setup"] == setup:
                per_repeat.setdefault(r["repeat"], []).append(r)
        rates = []
        for repeat in sorted(per_repeat):
            entries = per_repeat[repeat]
            passed = sum(e["passed"] for e in entries)
            total = sum(e["total"] for e in entries)
            if total:
                rates.append(round(100 * passed / total, 1))
        if rates:
            print(f"  {setup:14s} n={len(rates)} repeats  rates={rates}  "
                  f"mean={sum(rates)/len(rates):.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
