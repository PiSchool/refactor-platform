"""Embedding and reranking adapters.

Embeddings come from the served code model, which is too large to load inside the
API process. `load_embedder` builds a replacement when a deployment produces
embeddings elsewhere; anything it returns implements the same contract:
`embed_documents`, `embed_queries`, `model_name`, `dimension`.

The cross-encoder reranker is small enough to run in this process.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from threading import Lock
from typing import Iterable

from app.retrieval.errors import RetrievalUnavailable


def load_embedder(config):
    """Build the embedder named by `RETRIEVAL_EMBEDDER` as `module:function`.

    The function receives the retrieval configuration and returns the embedder.
    A bad reference fails here rather than half way through an index build.
    """
    import importlib

    reference = config.embedder_factory
    module_name, _, attribute = reference.partition(":")
    if not module_name or not attribute:
        raise RetrievalUnavailable(
            f"RETRIEVAL_EMBEDDER must look like 'module:function', got {reference!r}"
        )
    try:
        factory = getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError) as exc:
        raise RetrievalUnavailable(f"embedder {reference!r} could not be loaded: {exc}") from exc
    embedder = factory(config)
    missing = [
        name for name in ("embed_documents", "embed_queries", "model_name", "dimension")
        if not hasattr(embedder, name)
    ]
    if missing:
        raise RetrievalUnavailable(
            f"embedder {reference!r} is missing {', '.join(missing)}"
        )
    return embedder


class OllamaEmbedder:
    """The study's embedding path: one HTTP call per batch to an Ollama server.

    Ollama loads the model once and keeps it resident, so the API process stays
    small no matter how large the embedding model is. Failures are raised, never
    absorbed: an index built from partially embedded chunks would be silently
    wrong for the rest of its life.
    """

    device = "ollama"

    def __init__(self, model_name: str, dimension: int, host: str, *,
                 num_ctx: int = 2048, num_batch: int = 2048, max_chars: int = 500,
                 batch_size: int = 16, timeout: float = 120.0, attempts: int = 3,
                 transport=None):
        self.model_name = model_name
        self.dimension = dimension
        self.host = host.rstrip("/")
        self.num_ctx = num_ctx
        self.num_batch = num_batch
        self.max_chars = max(1, max_chars)
        self.batch_size = max(1, batch_size)
        self.timeout = timeout
        self.attempts = max(1, attempts)
        # injected in tests; production uses urllib
        self._transport = transport or self._post

    def _post(self, url: str, payload: dict) -> dict:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.load(response)

    def _call(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self.model_name,
            "input": texts,
            "options": {"num_ctx": self.num_ctx, "num_batch": self.num_batch},
        }
        last: Exception | None = None
        for attempt in range(self.attempts):
            try:
                body = self._transport(f"{self.host}/api/embed", payload)
                break
            except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
                last = exc
                if attempt + 1 < self.attempts:
                    time.sleep(min(2.0 * (attempt + 1), 5.0))
        else:
            raise RetrievalUnavailable(
                f"Ollama embedding request failed after {self.attempts} attempts "
                f"({self.host}, model {self.model_name}): {last}"
            )
        vectors = body.get("embeddings") or ([body["embedding"]] if body.get("embedding") else [])
        if len(vectors) != len(texts):
            raise RetrievalUnavailable(
                f"Ollama returned {len(vectors)} embeddings for {len(texts)} inputs"
            )
        return [[float(value) for value in vector] for vector in vectors]

    def _embed(self, texts: Iterable[str]) -> list:
        values = [str(text)[: self.max_chars] for text in texts]
        if not values:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(values), self.batch_size):
            vectors.extend(self._call(values[start:start + self.batch_size]))
        wrong = [len(vector) for vector in vectors if len(vector) != self.dimension]
        if wrong:
            raise RetrievalUnavailable(
                f"embedding dimension mismatch: configured {self.dimension}, "
                f"received {wrong[0]} from {self.model_name}"
            )
        return vectors

    def embed_documents(self, texts: Iterable[str]) -> list:
        return self._embed(texts)

    def embed_queries(self, texts: Iterable[str]) -> list:
        return self._embed(texts)


class CpuFastReranker:
    device = "cpu"

    def __init__(self, model_name: str, cache_dir: Path, threads: int = 4):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.threads = max(1, threads)
        self._model = None
        self._lock = Lock()

    def _load(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                from fastembed.rerank.cross_encoder import TextCrossEncoder
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self._model = TextCrossEncoder(
                    model_name=self.model_name,
                    cache_dir=str(self.cache_dir),
                    providers=["CPUExecutionProvider"],
                    threads=self.threads,
                )
            except Exception as exc:
                raise RetrievalUnavailable(f"CPU reranker unavailable: {exc}") from exc
        return self._model

    def rerank(self, query: str, documents: Iterable[str]) -> list[float]:
        values = list(documents)
        if not values:
            return []
        try:
            return [float(score) for score in self._load().rerank(query, values, batch_size=4)]
        except RetrievalUnavailable:
            raise
        except Exception as exc:
            raise RetrievalUnavailable(f"CPU reranking failed: {exc}") from exc