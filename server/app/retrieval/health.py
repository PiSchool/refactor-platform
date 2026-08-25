"""Cheap, redacted S2 health and system information."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.retrieval.config import RetrievalConfig
from app.retrieval.store import PostgresHybridStore


def status(probe_database: bool = False) -> dict:
    config = RetrievalConfig.from_environment()
    value = {
        "configured": bool(config.database_url),
        "status": "not_configured" if not config.database_url else "configured",
        "embeddingModel": config.embedding_model,
        "embeddingDimension": config.embedding_dimension,
        "embeddingsServedBy": config.embedder_factory or config.ollama_host,
        "rerankerModel": config.reranker_model,
        "queryExpansion": (
            f"llm:{config.expansion_model}" if config.expansion_model
            else "deterministic-identifiers-v1"
        ),
    }
    if config.embedder_factory:
        value["embeddingHostStatus"] = "ready"
    else:
        value["embeddingHost"] = config.ollama_host
        state, detail = _ollama_state(config)
        value["embeddingHostStatus"] = detail
        if state != "ready":
            # Two different situations, and reporting them alike was wrong. A
            # model server that is up and still fetching its weights is a first
            # start in progress; one that cannot be reached is a deployment
            # fault. Only the second is a failure.
            value["status"] = state
            value.setdefault("error" if state == "error" else "detail", detail)
    if probe_database and config.database_url:
        try:
            database = PostgresHybridStore(
                config.database_url, config.embedding_dimension
            ).health()
            # The store reports whether *the database* is ready, and merging it
            # wholesale used to overwrite a model server that was still fetching
            # its weights. The overall status then read `ready` while every S2 run
            # was being refused, which is the one situation this field exists to
            # warn about. Retrieval needs every layer, so the weakest one decides.
            if value["status"] in ("provisioning", "error"):
                database.pop("status", None)
            value.update(database)
        except Exception as exc:
            value["status"] = "error"
            value["error"] = str(exc)[:300]
    return value


def _ollama_state(config: RetrievalConfig, timeout: float = 5.0) -> tuple[str, str]:
    """`ready`, `provisioning` or `error`, and why.

    The distinction decides whether the platform reports itself unhealthy: a
    reachable server without the model yet is the first start pulling several
    gigabytes, which finishes on its own.
    """
    try:
        with urllib.request.urlopen(f"{config.ollama_host}/api/tags", timeout=timeout) as response:
            names = {
                str(model.get("name", ""))
                for model in json.load(response).get("models", [])
            }
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        return "error", f"unreachable at {config.ollama_host}: {str(exc)[:160]}"
    wanted = config.embedding_model
    if wanted in names or any(name.split(":")[0] == wanted.split(":")[0] for name in names):
        return "ready", "ready"
    return "provisioning", (
        f"{config.ollama_host} is up and does not have {wanted} yet; "
        "S2 and S3 runs are refused until the pull finishes"
    )


def retrieval_rows() -> list[dict[str, str]]:
    """The stages a query passes through, in order, with this deployment's limits."""
    config = RetrievalConfig.from_environment()
    value = status(probe_database=True)
    ok = value["status"] in ("ready", "configured")
    rows = [
        {
            "name": "Model server",
            "value": str(value["embeddingsServedBy"]),
            "state": "ok" if value.get("embeddingHostStatus") == "ready" else "absent",
            "detail": (
                str(value.get("embeddingHostStatus", ""))
                if value.get("embeddingHostStatus") != "ready"
                else "serves the embedding and query-rewriting models; S2 and S3 need it"
            ),
        },
        {
            "name": "Index",
            "value": f"{value.get('indexes', 0)} indexed repositories",
            "state": "ok" if ok else "absent",
            "detail": str(value.get("error") or value.get("detail") or value["status"]),
        },
        {
            "name": "Chunking",
            "value": "functions and classes",
            "state": "ok",
            "detail": ("parsed per language \u2014 ast for Python, tree-sitter for Java \u2014 with "
                       f"{config.window_lines}-line windows overlapping by {config.overlap_lines} "
                       "elsewhere"),
        },
        {
            "name": "Dense search",
            "value": f"{value['embeddingModel']} \u2192 top {config.vector_candidates}",
            "state": "ok",
            "detail": (
                f"{value['embeddingDimension']}-dimensional vectors in pgvector, "
                + ("scanned exactly \u2014 pgvector indexes at most 2000 dimensions"
                   if value.get("denseSearch") == "exact" else "searched through an HNSW index")
            ),
        },
        {
            "name": "Lexical search",
            "value": f"BM25 \u2192 top {config.lexical_candidates}",
            "state": "ok",
            "detail": (f"over the same chunks, prefiltered to {config.prefilter_candidates} "
                       "by symbol and path"),
        },
        {
            "name": "Fusion",
            "value": f"reciprocal rank \u2192 top {config.fused_candidates}",
            "state": "ok",
            "detail": "both rankings combined by rank, not by comparing their scores",
        },
        {
            "name": "Rerank",
            "value": f"{value['rerankerModel']} \u2192 top {config.context_hits}",
            "state": "ok",
            "detail": (f"cross-encoder in this process over the query and each candidate, "
                       f"within a {config.context_char_limit:,} character budget"),
        },
        {
            "name": "Query expansion",
            "value": str(value["queryExpansion"]),
            "state": "ok",
            "detail": (
                "the task instructions are rewritten into queries by a model"
                if str(value["queryExpansion"]).startswith("llm:")
                else "identifiers taken from the task instructions, no model call"
            ),
        },
    ]
    return rows
