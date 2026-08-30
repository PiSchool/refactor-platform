"""A deterministic embedder for the tests, loaded through `RETRIEVAL_EMBEDDER`.

The shipped stack serves embeddings from the model server, which a test run does
not have. Rather than skip retrieval, or hide a fake inside the product, the
tests use the same hook a deployment would use to plug in its own embedder: this
module hashes text into a fixed-length vector, so indexing, hybrid search,
fusion, reranking and the MCP tools all run for real and reproducibly.
"""
from __future__ import annotations

import hashlib
import math
from typing import Iterable

DIMENSION = 64
MODEL_NAME = "fixture-hash-v1"


class HashEmbedder:
    """Token-frequency vectors, L2-normalised. Same text, same vector, always."""

    model_name = MODEL_NAME
    dimension = DIMENSION

    def __init__(self, dimension: int = DIMENSION, model_name: str = MODEL_NAME):
        self.dimension = dimension
        self.model_name = model_name

    def _vector(self, text: str) -> list[float]:
        values = [0.0] * self.dimension
        tokens = [token for token in _tokenize(text) if token]
        for token in tokens or ["\x00"]:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            values[digest[0] % self.dimension] += 1.0
            values[digest[1] % self.dimension] += 0.5
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_queries(self, texts: Iterable[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]


def _tokenize(text: str) -> list[str]:
    token, tokens = [], []
    for character in text.lower():
        if character.isalnum() or character == "_":
            token.append(character)
        elif token:
            tokens.append("".join(token))
            token = []
    if token:
        tokens.append("".join(token))
    return tokens


def build(_config) -> HashEmbedder:
    return HashEmbedder()
