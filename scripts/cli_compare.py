"""Run the same RefactorBench tasks under several agent CLIs and compare them.

    python3 scripts/cli_compare.py launch [--model M] [--clis "codex claude opencode"]
    python3 scripts/cli_compare.py report RUN_ID [RUN_ID ...]

Same tasks, same model, same setup (s1): the CLI is the only variable. TASKS
are the descriptive-mode tasks that no S1 configuration of the study solved and
retrieval solved at least once. `report` waits for the runs to finish and prints
pass counts, tokens, list-price cost and agent time, then the per-task verdicts.
Talks to the API on PLATFORM_API (default http://127.0.0.1:8000).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

API = os.environ.get("PLATFORM_API", "http://127.0.0.1:8000") + "/api"
PRICE = {"qwen/qwen3.6-flash": (0.25, 1.50)}  # $ per million tokens in, out
TASKS = [
    "ansible_refactor/combine-namespace-compat#descriptive",
    "celery_refactor/combine-unpickle-task#descriptive",
    "tornado_refactor/global-objects#descriptive",
    "tornado_refactor/options-utils#descriptive",
    "scrapy_refactor/new-verify-reactor-class#descriptive",
    "scrapy_refactor/rename-description-commands#descriptive",
    "fastapi_refactor/openapi-get-utils#descriptive",
    "django_refactor/add-log-parameter-constant-time-compare#descriptive",
    "django_refactor/new-timezone-class#descriptive",
    "requests_refactor/combine-from-key-to-key#descriptive",
]


def call(path: str, body: dict | None = None):
    request = urllib.request.Request(
        API + path, method="POST" if body else "GET",
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def tasks_of(run_id: str) -> list[dict]:
    data = call(f"/runs/{run_id}/tasks")
    return data if isinstance(data, list) else data["tasks"]


def launch(model: str, clis: list[str]) -> None:
    catalog = call("/catalog")
    bench = next(b for b in catalog["benchmarks"] if b["key"] == "refbench")
    agents = {a["key"]: a for a in catalog["agents"]}
    ids = []
    for key in clis:
        if not agents[key].get("available"):
            print(f"skip {key}: {agents[key]['binary']} is not installed")
            continue
        run = call("/runs", {"benchmarkId": bench["id"], "setupId": "s1",
                             "agentToolId": agents[key]["id"], "model": model,
                             "taskKeys": TASKS, "taskTimeoutSeconds": 900})
        ids.append(run["id"])
        print(f"{key:<9} -> run {run['id']}")
    print("python3 scripts/cli_compare.py report " + " ".join(ids))


def report(run_ids: list[str]) -> None:
    while True:
        runs = [call(f"/runs/{run_id}") for run_id in run_ids]
        if all(run["status"] in ("completed", "failed", "stopped") for run in runs):
            break
        print("waiting:", ", ".join(f"{r['agentTool']['key']} {r['counts']['pending']} left" for r in runs),
              flush=True)
        time.sleep(30)

    print(f"\n{'CLI':<20}{'passed':>8}{'in':>10}{'out':>9}{'cost':>8}{'agent':>8}")
    grid: dict[str, dict[str, str]] = {}
    for run in runs:
        rows = tasks_of(run["id"])
        results = [row.get("result") or {} for row in rows]
        tokens_in = sum(r.get("tokensInput") or 0 for r in results)
        tokens_out = sum(r.get("tokensOutput") or 0 for r in results)
        price_in, price_out = PRICE.get(run["model"], (0.0, 0.0))
        cost = (tokens_in * price_in + tokens_out * price_out) / 1e6
        minutes = sum(r.get("agentSeconds") or 0 for r in results) / 60
        name = run["agentTool"]["name"]
        print(f"{name:<20}{run['counts']['passed']:>5}/{len(rows):<2}{tokens_in / 1e6:>9.2f}M"
              f"{tokens_out / 1e3:>8.1f}k{cost:>7.2f}${minutes:>6.0f}m")
        for row in rows:
            tests = ((row.get("result") or {}).get("details") or {}).get("python_tests") or {}
            message = tests.get("message", "") if isinstance(tests, dict) else ""
            grid.setdefault(row["taskKey"].split("#")[0], {})[name] = (
                "pass" if row["status"] == "passed" else message.split(" ")[0] or row["status"])

    names = [run["agentTool"]["name"] for run in runs]
    print(f"\n{'task':<56}" + "".join(f"{n[:12]:>14}" for n in names))
    for task, cells in grid.items():
        print(f"{task:<56}" + "".join(f"{cells.get(n, '-'):>14}" for n in names))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["launch"]:
        model = args[args.index("--model") + 1] if "--model" in args else "qwen/qwen3.6-flash"
        clis = (args[args.index("--clis") + 1] if "--clis" in args else "codex claude opencode").split()
        launch(model, clis)
    elif args[:1] == ["report"] and args[1:]:
        report(args[1:])
    else:
        sys.exit(__doc__)
