"""Query expansion.

Two ways to turn a task's instructions into searches. The deterministic planner
in `ranking.plan_queries` derives a broad, an identifier and a target query from
the text itself; it is reproducible and needs nothing but the task.

The study also ran a second, generative expansion: a small instruction-tuned
code model rewrites the task into additional searches, which recovers vocabulary
the instructions never use. That path runs whenever `retrieval.expansion_model`
names a model, and it fails closed — if the configured model cannot deliver the
rewrite, the run stops rather than quietly becoming a different experiment.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from app.retrieval.errors import RetrievalUnavailable
from app.retrieval.models import QuerySpec

_PROMPT = (
    "You are helping a code search engine locate the code a refactoring task "
    "will have to change.\n"
    "Write {count} short search queries for the task below. One query per line, "
    "no numbering, no explanation. Prefer identifiers, type names, method names "
    "and file paths over prose.\n\nTask:\n{task}\n"
)
_MAX_QUERY_CHARS = 200
_LEADING_MARKER = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s*")


def _post(url: str, payload: dict, timeout: float) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def parse_queries(text: str, limit: int) -> list[str]:
    """Lines out of a chat completion, with the usual list decorations removed."""
    queries: list[str] = []
    for raw in str(text or "").splitlines():
        line = _LEADING_MARKER.sub("", raw).strip().strip("`\"'")
        if not line or line.endswith(":"):
            continue
        queries.append(line[:_MAX_QUERY_CHARS])
        if len(queries) >= limit:
            break
    return list(dict.fromkeys(queries))


def expand(
    instructions: str,
    *,
    model: str,
    host: str,
    count: int = 3,
    timeout: float = 120.0,
    attempts: int = 2,
    transport=None,
) -> list[QuerySpec]:
    """Additional queries from the expansion model, as `expanded-N` specs."""
    task = " ".join(str(instructions or "").split())[:4000]
    if not task:
        return []
    call = transport or (lambda url, payload: _post(url, payload, timeout))
    payload = {
        "model": model,
        "prompt": _PROMPT.format(count=count, task=task),
        "stream": False,
        # deterministic decoding: the same task must expand the same way twice
        "options": {"temperature": 0.0, "num_predict": 256},
    }
    last: Exception | None = None
    for attempt in range(max(1, attempts)):
        try:
            body = call(f"{host.rstrip('/')}/api/generate", payload)
            break
        except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
            last = exc
    else:
        raise RetrievalUnavailable(
            f"query expansion model {model!r} unreachable at {host}: {last}"
        )

    queries = parse_queries(body.get("response", ""), count)
    if not queries:
        raise RetrievalUnavailable(
            f"query expansion model {model!r} returned no usable queries"
        )
    return [QuerySpec(f"expanded-{index}", query) for index, query in enumerate(queries, start=1)]
