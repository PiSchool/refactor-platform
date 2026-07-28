"""Persistent pgvector store and a behaviorally equivalent test store."""
from __future__ import annotations

import math
import threading
from collections import Counter
from typing import Protocol, Sequence

from app.retrieval.errors import RetrievalUnavailable
from app.retrieval.models import CodeChunk, IndexIdentity, RankedChunk
from app.retrieval.ranking import bm25_rank, tokenize


class HybridStore(Protocol):
    connection_url: str

    def has_exact(self, identity: IndexIdentity) -> bool: ...
    def replace(self, identity: IndexIdentity, chunks: Sequence[CodeChunk],
                embeddings: Sequence[Sequence[float]], metadata: dict) -> None: ...
    def manifest(self, index_key: str) -> dict: ...
    def all_chunks(self, index_key: str) -> list[CodeChunk]: ...
    def fetch_chunks(self, index_key: str, chunk_ids: Sequence[str]) -> list[CodeChunk]: ...
    def vector_rank(self, index_key: str, embedding: Sequence[float], top_k: int) -> list[RankedChunk]: ...
    def lexical_rank(self, index_key: str, query: str, top_k: int) -> list[RankedChunk]: ...
    def list_files(self, index_key: str) -> list[str]: ...


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


class InMemoryHybridStore:
    connection_url = ""

    def __init__(self):
        self._indexes: dict[str, dict] = {}
        self.build_count = 0

    def has_exact(self, identity: IndexIdentity) -> bool:
        row = self._indexes.get(identity.key)
        return bool(row and row["identity"] == identity.to_dict() and row["chunks"])

    def replace(self, identity, chunks, embeddings, metadata):
        self._indexes[identity.key] = {
            "identity": identity.to_dict(),
            "chunks": list(chunks),
            "embeddings": [list(vector) for vector in embeddings],
            "metadata": dict(metadata),
        }
        self.build_count += 1

    def manifest(self, index_key: str) -> dict:
        row = self._indexes[index_key]
        return {**row["identity"], **row["metadata"], "chunkCount": len(row["chunks"])}

    def all_chunks(self, index_key: str) -> list[CodeChunk]:
        return list(self._indexes[index_key]["chunks"])

    def fetch_chunks(self, index_key: str, chunk_ids: Sequence[str]) -> list[CodeChunk]:
        wanted = set(chunk_ids)
        return [chunk for chunk in self.all_chunks(index_key) if chunk.chunk_id in wanted]

    def vector_rank(self, index_key: str, embedding: Sequence[float], top_k: int) -> list[RankedChunk]:
        row = self._indexes[index_key]
        ranked = [
            RankedChunk(chunk.chunk_id, _cosine(embedding, vector))
            for chunk, vector in zip(row["chunks"], row["embeddings"], strict=True)
        ]
        ranked.sort(key=lambda hit: (-hit.score, hit.chunk_id))
        return ranked[:top_k]

    def lexical_rank(self, index_key: str, query: str, top_k: int) -> list[RankedChunk]:
        return bm25_rank(self.all_chunks(index_key), query, top_k)

    def list_files(self, index_key: str) -> list[str]:
        return sorted({chunk.path for chunk in self.all_chunks(index_key)})


#: pgvector's limit for a stored `vector`.
VECTOR_STORAGE_LIMIT = 16000
#: pgvector's limit for an HNSW or IVFFlat index over a `vector`. A model above
#: it is searched exactly instead: refusing it would have made the study's own
#: embedding model (3584 dimensions) unusable, which is what happened here.
VECTOR_INDEX_LIMIT = 2000


class PostgresHybridStore:
    """pgvector cosine search plus persisted text for exact BM25 ranking."""

    def __init__(self, connection_url: str, dimension: int, *, read_only: bool = False):
        if not connection_url.startswith(("postgresql://", "postgres://")):
            raise RetrievalUnavailable(
                "S2 requires RETRIEVAL_DATABASE_URL (or DATABASE_URL) to use PostgreSQL/pgvector"
            )
        if dimension < 1 or dimension > VECTOR_STORAGE_LIMIT:
            raise RetrievalUnavailable(
                f"pgvector stores at most {VECTOR_STORAGE_LIMIT} dimensions per vector; "
                f"the configured embedding model emits {dimension}"
            )
        self.connection_url = connection_url
        self.dimension = dimension
        self.read_only = read_only
        self._schema_ready = False
        self._schema_lock = threading.Lock()

    def _connect(self, *, register_types: bool = True):
        try:
            import psycopg

            connection = psycopg.connect(self.connection_url, connect_timeout=5)
            if register_types:
                from pgvector.psycopg import register_vector
                register_vector(connection)
            return connection
        except Exception as exc:
            raise RetrievalUnavailable(f"pgvector connection unavailable: {exc}") from exc

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        with self._schema_lock:
            if self._schema_ready:
                return
            if self.read_only:
                with self._connect() as conn:
                    row = conn.execute(
                        """SELECT to_regclass('public.retrieval_indexes'),
                                  to_regclass('public.retrieval_chunks')"""
                    ).fetchone()
                    if not row or not all(row):
                        raise RetrievalUnavailable("retrieval schema is not initialized")
                self._schema_ready = True
                return
            # A fresh database does not expose vector types until the extension
            # exists, so codec registration must happen after CREATE EXTENSION.
            with self._connect(register_types=False) as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                from pgvector.psycopg import register_vector
                register_vector(conn)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS retrieval_indexes (
                        index_key text PRIMARY KEY,
                        manifest jsonb NOT NULL,
                        metadata jsonb NOT NULL,
                        chunk_count integer NOT NULL,
                        status text NOT NULL CHECK (status IN ('building', 'ready')),
                        created_at timestamptz NOT NULL DEFAULT now()
                    )
                """)
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS retrieval_chunks (
                        index_key text NOT NULL REFERENCES retrieval_indexes(index_key) ON DELETE CASCADE,
                        chunk_id text NOT NULL,
                        path text NOT NULL,
                        start_line integer NOT NULL,
                        end_line integer NOT NULL,
                        symbol text NOT NULL,
                        language text NOT NULL,
                        content text NOT NULL,
                        token_counts jsonb NOT NULL,
                        token_count integer NOT NULL,
                        embedding vector NOT NULL,
                        embedding_dimension integer NOT NULL,
                        PRIMARY KEY (index_key, chunk_id)
                    )
                """)
                # Migrate the original fixed-dimension schema in place. A plain
                # vector column can retain old indexes while new model dimensions
                # receive their own partial expression indexes.
                conn.execute("DROP INDEX IF EXISTS retrieval_chunks_embedding_hnsw")
                columns = {
                    row[0] for row in conn.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = 'retrieval_chunks'
                    """).fetchall()
                }
                if "embedding_dimension" not in columns:
                    conn.execute(
                        "ALTER TABLE retrieval_chunks ADD COLUMN embedding_dimension integer"
                    )
                    conn.execute("""
                        UPDATE retrieval_chunks AS chunk
                        SET embedding_dimension = coalesce(
                            (idx.manifest ->> 'embedding_dimension')::integer, %s
                        )
                        FROM retrieval_indexes AS idx
                        WHERE chunk.index_key = idx.index_key
                          AND chunk.embedding_dimension IS NULL
                    """, (self.dimension,))
                    conn.execute("""
                        ALTER TABLE retrieval_chunks
                        ALTER COLUMN embedding_dimension SET NOT NULL
                    """)
                embedding_type = conn.execute("""
                    SELECT format_type(attribute.atttypid, attribute.atttypmod)
                    FROM pg_attribute AS attribute
                    JOIN pg_class AS relation ON relation.oid = attribute.attrelid
                    WHERE relation.relname = 'retrieval_chunks'
                      AND attribute.attname = 'embedding'
                """).fetchone()[0]
                if embedding_type != "vector":
                    conn.execute("""
                        ALTER TABLE retrieval_chunks
                        ALTER COLUMN embedding TYPE vector USING embedding::vector
                    """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS retrieval_chunks_tokens_gin
                    ON retrieval_chunks USING gin (token_counts)
                """)
                self._ensure_dimension_index(conn)
            self._schema_ready = True

    @property
    def approximate(self) -> bool:
        """Whether this dimension can carry an approximate-search index."""
        return int(self.dimension) <= VECTOR_INDEX_LIMIT

    def _ensure_dimension_index(self, conn) -> None:
        dimension = int(self.dimension)
        if not self.approximate:
            # Above pgvector's index limit the query planner scans the partition
            # for this dimension and ranks every chunk exactly. Recall is total;
            # the cost is linear in corpus size, which is how the published study
            # searched its 3584-dimensional index.
            return
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS retrieval_chunks_embedding_{dimension}_hnsw
            ON retrieval_chunks USING hnsw
              ((embedding::vector({dimension})) vector_cosine_ops)
            WHERE embedding_dimension = {dimension}
        """)

    def health(self) -> dict:
        self._ensure_schema()
        with self._connect() as conn:
            version = conn.execute(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()
            count = conn.execute(
                "SELECT count(*) FROM retrieval_indexes WHERE status = 'ready'"
            ).fetchone()[0]
        return {
            "status": "ready",
            "pgvectorVersion": version[0],
            "indexes": int(count),
            # Whether dense search is approximate or exact follows from the
            # dimension, and a reader of the report should not have to know that.
            "denseSearch": "approximate" if self.approximate else "exact",
        }

    def has_exact(self, identity: IndexIdentity) -> bool:
        self._ensure_schema()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT manifest, chunk_count, status FROM retrieval_indexes WHERE index_key = %s",
                (identity.key,),
            ).fetchone()
        if not row:
            return False
        manifest, count, status = row
        return manifest == identity.to_dict() and int(count) > 0 and status == "ready"

    def replace(self, identity, chunks, embeddings, metadata):
        if self.read_only:
            raise RetrievalUnavailable("read-only retrieval store cannot modify indexes")
        self._ensure_schema()
        if len(chunks) != len(embeddings):
            raise RetrievalUnavailable("chunk/embedding count mismatch")
        try:
            import numpy as np
            from psycopg.types.json import Jsonb

            with self._connect() as conn:
                conn.execute("DELETE FROM retrieval_indexes WHERE index_key = %s", (identity.key,))
                conn.execute(
                    """INSERT INTO retrieval_indexes
                       (index_key, manifest, metadata, chunk_count, status)
                       VALUES (%s, %s, %s, %s, 'building')""",
                    (identity.key, Jsonb(identity.to_dict()), Jsonb(metadata), len(chunks)),
                )
                with conn.cursor() as cursor:
                    for start in range(0, len(chunks), 256):
                        rows = []
                        for chunk, embedding in zip(
                            chunks[start:start + 256], embeddings[start:start + 256], strict=True
                        ):
                            counts = Counter(tokenize(chunk.document))
                            rows.append((
                                identity.key, chunk.chunk_id, chunk.path, chunk.start_line,
                                chunk.end_line, chunk.symbol, chunk.language, chunk.text,
                                Jsonb(dict(counts)), sum(counts.values()),
                                np.asarray(embedding, dtype=np.float32), self.dimension,
                            ))
                        cursor.executemany(
                            """INSERT INTO retrieval_chunks
                               (index_key, chunk_id, path, start_line, end_line, symbol,
                                language, content, token_counts, token_count, embedding,
                                embedding_dimension)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            rows,
                        )
                conn.execute(
                    "UPDATE retrieval_indexes SET status = 'ready' WHERE index_key = %s",
                    (identity.key,),
                )
        except RetrievalUnavailable:
            raise
        except Exception as exc:
            raise RetrievalUnavailable(f"failed to persist pgvector index: {exc}") from exc

    def manifest(self, index_key: str) -> dict:
        self._ensure_schema()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT manifest, metadata, chunk_count FROM retrieval_indexes WHERE index_key = %s",
                (index_key,),
            ).fetchone()
        if not row:
            raise RetrievalUnavailable(f"retrieval index not found: {index_key}")
        return {**row[0], **row[1], "chunkCount": row[2]}

    @staticmethod
    def _chunk(row) -> CodeChunk:
        return CodeChunk(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

    def all_chunks(self, index_key: str) -> list[CodeChunk]:
        self._ensure_schema()
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT chunk_id, path, start_line, end_line, symbol, content, language
                   FROM retrieval_chunks WHERE index_key = %s ORDER BY chunk_id""",
                (index_key,),
            ).fetchall()
        return [self._chunk(row) for row in rows]

    def fetch_chunks(self, index_key: str, chunk_ids: Sequence[str]) -> list[CodeChunk]:
        if not chunk_ids:
            return []
        self._ensure_schema()
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT chunk_id, path, start_line, end_line, symbol, content, language
                   FROM retrieval_chunks WHERE index_key = %s AND chunk_id = ANY(%s)""",
                (index_key, list(chunk_ids)),
            ).fetchall()
        by_id = {row[0]: self._chunk(row) for row in rows}
        return [by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in by_id]

    def vector_rank(self, index_key: str, embedding: Sequence[float], top_k: int) -> list[RankedChunk]:
        self._ensure_schema()
        try:
            import numpy as np
            vector = np.asarray(embedding, dtype=np.float32)
            with self._connect() as conn:
                rows = conn.execute(
                    f"""SELECT chunk_id,
                               1 - ((embedding::vector({self.dimension})) <=> %s) AS similarity
                        FROM retrieval_chunks
                        WHERE index_key = %s AND embedding_dimension = %s
                        ORDER BY (embedding::vector({self.dimension})) <=> %s LIMIT %s""",
                    (vector, index_key, self.dimension, vector, top_k),
                ).fetchall()
            return [RankedChunk(row[0], float(row[1])) for row in rows]
        except RetrievalUnavailable:
            raise
        except Exception as exc:
            raise RetrievalUnavailable(f"pgvector search failed: {exc}") from exc

    def lexical_rank(
        self, index_key: str, query: str, top_k: int,
        *, k1: float = 1.5, b: float = 0.75,
    ) -> list[RankedChunk]:
        """Compute exact BM25 over GIN-selected token-count rows.

        Only token maps for chunks containing a query term cross the database
        boundary; source text and unrelated chunks are not loaded per query.
        """
        terms = list(dict.fromkeys(tokenize(query)))
        if not terms or top_k <= 0:
            return []
        self._ensure_schema()
        try:
            with self._connect() as conn:
                totals = conn.execute(
                    """SELECT count(*), coalesce(avg(token_count), 0)
                       FROM retrieval_chunks WHERE index_key = %s""",
                    (index_key,),
                ).fetchone()
                df_rows = conn.execute(
                    """SELECT term, count(chunk_id)
                       FROM unnest(%s::text[]) AS term
                       LEFT JOIN retrieval_chunks
                         ON index_key = %s AND token_counts ? term
                       GROUP BY term""",
                    (terms, index_key),
                ).fetchall()
                candidates = conn.execute(
                    """SELECT chunk_id, token_counts, token_count
                       FROM retrieval_chunks
                       WHERE index_key = %s AND token_counts ?| %s::text[]""",
                    (index_key, terms),
                ).fetchall()
            total, average_length = int(totals[0]), float(totals[1])
            document_frequency = {term: int(count) for term, count in df_rows}
            ranked: list[RankedChunk] = []
            for chunk_id, counts, length in candidates:
                score = 0.0
                for term in terms:
                    tf = int(counts.get(term, 0))
                    if not tf:
                        continue
                    df = document_frequency.get(term, 0)
                    idf = math.log(1.0 + (total - df + 0.5) / (df + 0.5))
                    denominator = tf + k1 * (
                        1.0 - b + b * int(length) / max(average_length, 1.0)
                    )
                    score += idf * (tf * (k1 + 1.0)) / denominator
                if score > 0:
                    ranked.append(RankedChunk(chunk_id, score))
            ranked.sort(key=lambda hit: (-hit.score, hit.chunk_id))
            return ranked[:top_k]
        except RetrievalUnavailable:
            raise
        except Exception as exc:
            raise RetrievalUnavailable(f"BM25 search failed: {exc}") from exc

    def list_files(self, index_key: str) -> list[str]:
        self._ensure_schema()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT path FROM retrieval_chunks WHERE index_key = %s ORDER BY path",
                (index_key,),
            ).fetchall()
        return [row[0] for row in rows]