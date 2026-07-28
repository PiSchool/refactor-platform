"""Read-only stdio MCP server over one immutable retrieval index."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from threading import Lock

from mcp.server.fastmcp import FastMCP

from app.retrieval.service import RetrievalService

mcp = FastMCP("Refactor Platform code retrieval")
_service: RetrievalService | None = None
_service_lock = Lock()


def _runtime() -> tuple[RetrievalService, str]:
    global _service
    index_key = os.environ.get("RETRIEVAL_INDEX_KEY", "").strip()
    if not index_key:
        raise RuntimeError("RETRIEVAL_INDEX_KEY is required")
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = RetrievalService.from_environment()
    return _service, index_key


def _record(tool: str, arguments: dict, result_count: int, elapsed: float) -> None:
    path_value = os.environ.get("RETRIEVAL_INVOCATIONS_PATH", "").strip()
    if not path_value:
        return
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": time.time(),
        "tool": tool,
        "arguments": arguments,
        "resultCount": result_count,
        "latencyMs": round(elapsed * 1000, 2),
        "device": "cpu",
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


@mcp.tool()
def search_codebase(query: str, top_k: int = 8) -> list[dict]:
    """Search indexed code with semantic vectors, BM25, RRF, and CPU reranking."""
    started = time.monotonic()
    service, index_key = _runtime()
    hits = service.search_existing(index_key, query, max(1, min(top_k, 20)))
    result = [hit.to_dict() for hit in hits]
    _record("search_codebase", {"query": query, "top_k": top_k}, len(result), time.monotonic() - started)
    return result


@mcp.tool()
def search_file(path: str, query: str, top_k: int = 8) -> list[dict]:
    """Search indexed code and keep only chunks from one repository-relative path."""
    started = time.monotonic()
    service, index_key = _runtime()
    candidates = service.search_existing(index_key, f"{path} {query}", 20)
    result = [hit.to_dict() for hit in candidates if hit.chunk.path == path][:max(1, min(top_k, 20))]
    _record(
        "search_file", {"path": path, "query": query, "top_k": top_k},
        len(result), time.monotonic() - started,
    )
    return result


@mcp.tool()
def list_indexed_files() -> list[str]:
    """List repository-relative source files available in the current index."""
    started = time.monotonic()
    service, index_key = _runtime()
    files = service.store.list_files(index_key)
    _record("list_indexed_files", {}, len(files), time.monotonic() - started)
    return files


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()