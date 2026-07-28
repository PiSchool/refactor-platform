"""Database-backed S2 store integration test (opt-in outside Compose)."""
from __future__ import annotations

import os
import uuid

import pytest


@pytest.mark.integration
def test_pgvector_store_round_trip_and_exact_readiness():
    url = os.getenv("RETRIEVAL_TEST_DATABASE_URL", "").strip()
    if not url:
        pytest.skip("RETRIEVAL_TEST_DATABASE_URL is not configured")

    from app.retrieval.models import CodeChunk, IndexIdentity
    from app.retrieval.store import PostgresHybridStore

    store = PostgresHybridStore(url, 768)
    suffix = uuid.uuid4().hex
    identity = IndexIdentity(
        "fixture", f"repo-{suffix}", "deadbeef", "python", "ast",
        "cpu-test-embedding", 768, "test-v1",
    )
    chunks = [
        CodeChunk(f"a-{suffix}", "auth.py", 1, 2, "validate_token",
                  "def validate_token(token): return bool(token)\n", "python"),
        CodeChunk(f"b-{suffix}", "math.py", 1, 2, "multiply",
                  "def multiply(a, b): return a * b\n", "python"),
    ]
    vectors = [
        [1.0, *([0.0] * 767)],
        [0.0, 1.0, *([0.0] * 766)],
    ]

    store.replace(identity, chunks, vectors, {"device": "cpu"})

    assert store.has_exact(identity)
    changed = IndexIdentity(
        identity.benchmark, identity.source, identity.revision, identity.language,
        "naive", identity.embedding_model, identity.embedding_dimension,
        identity.chunker_version,
    )
    assert not store.has_exact(changed)
    assert store.vector_rank(identity.key, vectors[0], 1)[0].chunk_id == chunks[0].chunk_id
    assert store.lexical_rank(identity.key, "validate_token", 1)[0].chunk_id == chunks[0].chunk_id
    assert {chunk.path for chunk in store.all_chunks(identity.key)} == {"auth.py", "math.py"}
    assert store.health()["pgvectorVersion"]

    # Model upgrades may change dimensions. The unbounded column and partial
    # HNSW indexes must preserve old vectors while serving the new dimension.
    compact = PostgresHybridStore(url, 3)
    compact_identity = IndexIdentity(
        "fixture", f"compact-{suffix}", "cafebabe", "python", "ast",
        "compact-cpu-model", 3, "test-v1",
    )
    compact_chunk = CodeChunk(
        f"c-{suffix}", "compact.py", 1, 1, "compact", "compact = True\n", "python"
    )
    compact.replace(compact_identity, [compact_chunk], [[0.0, 0.0, 1.0]], {"device": "cpu"})
    assert compact.vector_rank(compact_identity.key, [0.0, 0.0, 1.0], 1)[0].chunk_id == compact_chunk.chunk_id
    assert store.vector_rank(identity.key, vectors[0], 1)[0].chunk_id == chunks[0].chunk_id