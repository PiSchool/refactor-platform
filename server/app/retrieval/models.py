"""Small immutable data contracts for indexing and ranking."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CodeChunk:
    chunk_id: str
    path: str
    start_line: int
    end_line: int
    symbol: str
    text: str
    language: str = ""

    @property
    def document(self) -> str:
        return f"File: {self.path}\nSymbol: {self.symbol}\n{self.text}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChunkingReport:
    strategy: str
    files_seen: int
    files_indexed: int
    chunks: int
    fallback_files: int = 0
    skipped_files: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndexIdentity:
    benchmark: str
    source: str
    revision: str
    language: str
    strategy: str
    embedding_model: str
    embedding_dimension: int
    chunker_version: str
    scope: str = "repository"

    @property
    def key(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "key": self.key}


@dataclass(frozen=True)
class QuerySpec:
    kind: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RankedChunk:
    chunk_id: str
    score: float


@dataclass(frozen=True)
class FusedRank:
    chunk_id: str
    rrf_score: float
    appearances: int


@dataclass
class SearchHit:
    chunk: CodeChunk
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    query_kinds: list[str] = field(default_factory=list)

    @property
    def chunk_id(self) -> str:
        return self.chunk.chunk_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.chunk.to_dict(),
            "rrfScore": round(self.rrf_score, 8),
            "rerankScore": round(self.rerank_score, 8),
            "queryKinds": list(self.query_kinds),
        }