"""Identifier-aware query planning, exact BM25, and reciprocal-rank fusion."""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from pathlib import PurePosixPath
from typing import Iterable, Sequence

from app.retrieval.models import CodeChunk, FusedRank, QuerySpec, RankedChunk

_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_.$:/\\-]*|\d+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_BACKTICK = re.compile(r"`([^`]+)`")
_PATH = re.compile(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")
_STOP = {
    "a", "an", "and", "as", "at", "be", "by", "for", "from", "in", "into", "is",
    "it", "of", "on", "or", "the", "this", "to", "update", "with", "without",
}


def tokenize(text: str) -> list[str]:
    """Split prose plus snake/camel/dotted identifiers without losing exact IDs."""
    output: list[str] = []
    for raw in _WORD.findall(text):
        normalized = raw.strip("./:$\\-").lower()
        if not normalized:
            continue
        if normalized not in _STOP:
            output.append(normalized)
        for dotted in re.split(r"[./:$\\-]+", raw):
            for snake in dotted.split("_"):
                for part in _CAMEL.split(snake):
                    token = part.lower().strip()
                    if len(token) > 1 and token not in _STOP:
                        output.append(token)
    return output


def plan_queries(instructions: str, params: dict) -> list[QuerySpec]:
    """Produce the paper's broad, identifier, and target-oriented searches.

    The CPU release uses deterministic expansion rather than a second LLM. The
    generated queries and method are persisted, so this is auditable.
    """
    broad = " ".join(instructions.split())[:1200]
    quoted = [value.strip() for value in _BACKTICK.findall(instructions) if value.strip()]
    identifier_candidates = quoted + [
        token for token in _WORD.findall(instructions)
        if "_" in token or any(char.isupper() for char in token[1:])
    ]
    identifiers = list(dict.fromkeys(identifier_candidates))[:16]
    identifier_text = " ".join(identifiers) or " ".join(tokenize(broad)[:16])

    target_candidates: list[str] = []
    for key in ("filePathBefore", "filePathAfter", "path", "targetFile"):
        value = params.get(key)
        if isinstance(value, str) and value.strip():
            target_candidates.append(value.strip())
    target_candidates.extend(_PATH.findall(instructions))
    targets = list(dict.fromkeys(target_candidates))[:8]
    target_terms = []
    for target in targets:
        target_terms.extend((target, PurePosixPath(target).name, PurePosixPath(target).stem))
    target_text = " ".join(dict.fromkeys(target_terms)) or identifier_text
    return [
        QuerySpec("broad", broad),
        QuerySpec("identifier", identifier_text),
        QuerySpec("target", target_text),
    ]


def bm25_rank(
    chunks: Sequence[CodeChunk], query: str, top_k: int = 50,
    *, k1: float = 1.5, b: float = 0.75,
) -> list[RankedChunk]:
    """Rank chunks with Okapi BM25 over identifier-aware tokens."""
    if not chunks or top_k <= 0:
        return []
    query_terms = list(dict.fromkeys(tokenize(query)))
    if not query_terms:
        return []
    documents = [Counter(tokenize(chunk.document)) for chunk in chunks]
    lengths = [sum(doc.values()) for doc in documents]
    average_length = sum(lengths) / max(len(lengths), 1)
    frequencies = Counter(term for term in query_terms for doc in documents if term in doc)
    ranked: list[RankedChunk] = []
    total = len(chunks)
    for chunk, doc, length in zip(chunks, documents, lengths, strict=True):
        score = 0.0
        for term in query_terms:
            tf = doc.get(term, 0)
            if not tf:
                continue
            df = frequencies[term]
            idf = math.log(1.0 + (total - df + 0.5) / (df + 0.5))
            denominator = tf + k1 * (1.0 - b + b * length / max(average_length, 1.0))
            score += idf * (tf * (k1 + 1.0)) / denominator
        if score > 0:
            ranked.append(RankedChunk(chunk.chunk_id, score))
    ranked.sort(key=lambda hit: (-hit.score, hit.chunk_id))
    return ranked[:top_k]


def reciprocal_rank_fusion(
    rankings: Iterable[Sequence[str]], *, rank_constant: int = 60,
) -> list[FusedRank]:
    scores: dict[str, float] = defaultdict(float)
    appearances: Counter[str] = Counter()
    for ranking in rankings:
        seen: set[str] = set()
        for rank, chunk_id in enumerate(ranking, start=1):
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            scores[chunk_id] += 1.0 / (rank_constant + rank)
            appearances[chunk_id] += 1
    fused = [FusedRank(chunk_id, score, appearances[chunk_id]) for chunk_id, score in scores.items()]
    fused.sort(key=lambda item: (-item.rrf_score, -item.appearances, item.chunk_id))
    return fused