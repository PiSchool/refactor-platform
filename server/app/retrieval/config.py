"""What the retrieval runtime needs: the stack, and where to reach its services.

The models and the stage limits come from `config.yaml` (`retrieval:`), which is
their only definition. The environment carries what differs between deployments:
the two database URLs, the model server's address, the reranker's cache
directory, and an optional custom embedder.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

#: `module:function` returning an object with `embed_documents`, `embed_queries`,
#: `model_name` and `dimension`. Set to serve embeddings from something other
#: than the model server; the tests use it to embed deterministically.
EMBEDDER_ENV = "RETRIEVAL_EMBEDDER"


@dataclass(frozen=True)
class RetrievalConfig:
    database_url: str
    reader_database_url: str = ""
    embedding_model: str = ""
    embedding_dimension: int = 0
    reranker_model: str = ""
    expansion_model: str = ""
    ollama_host: str = "http://ollama:11434"
    embed_num_ctx: int = 2048
    embed_num_batch: int = 2048
    embed_max_chars: int = 500
    model_cache_dir: Path = Path("/data/models/fastembed")
    reranker_threads: int = 4
    prefilter_candidates: int = 512
    vector_candidates: int = 50
    lexical_candidates: int = 50
    fused_candidates: int = 40
    context_hits: int = 12
    context_char_limit: int = 24_000
    window_lines: int = 80
    overlap_lines: int = 20
    mcp_python: str = sys.executable
    embedder_factory: str = ""

    @classmethod
    def from_environment(cls, data_dir: Path | None = None) -> "RetrievalConfig":
        from app.config import get_settings

        platform = get_settings()
        stack = platform.retrieval
        root = data_dir or platform.data_dir
        raw_url = os.getenv("RETRIEVAL_DATABASE_URL") or os.getenv("DATABASE_URL", "")
        return cls(
            database_url=_sync_postgres_url(raw_url),
            reader_database_url=_sync_postgres_url(
                os.getenv("RETRIEVAL_READER_DATABASE_URL", "")
            ),
            embedding_model=stack.embedding_model,
            embedding_dimension=stack.embedding_dimension,
            reranker_model=stack.reranker_model,
            expansion_model=stack.expansion_model,
            ollama_host=_env("OLLAMA_HOST", "http://ollama:11434").rstrip("/"),
            embed_num_ctx=stack.embed_num_ctx,
            embed_num_batch=stack.embed_num_batch,
            embed_max_chars=stack.embed_max_chars,
            model_cache_dir=Path(_env(
                "RETRIEVAL_MODEL_CACHE_DIR", str(root / "models" / "fastembed")
            )),
            reranker_threads=stack.reranker_threads,
            prefilter_candidates=stack.prefilter_candidates,
            vector_candidates=stack.vector_candidates,
            lexical_candidates=stack.lexical_candidates,
            fused_candidates=stack.fused_candidates,
            context_hits=stack.context_hits,
            context_char_limit=stack.context_char_limit,
            window_lines=stack.window_lines,
            overlap_lines=stack.overlap_lines,
            embedder_factory=_env(EMBEDDER_ENV),
        )


def _env(name: str, default: str = "") -> str:
    """An unset or blank variable falls back: Compose renders every declared key,
    and a blank value must not erase a configured one."""
    return os.getenv(name, "").strip() or default


def _sync_postgres_url(url: str) -> str:
    if not url:
        return ""
    return url.replace("postgresql+asyncpg://", "postgresql://", 1).replace(
        "postgresql+psycopg://", "postgresql://", 1
    )
