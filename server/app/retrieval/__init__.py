"""CPU-only hybrid retrieval used by the S2 execution setups.

The package is platform-owned: benchmarks provide task text and workspace
identity, while retrieval owns chunking, indexing, search, and provenance.
"""

from app.retrieval.errors import RetrievalUnavailable
from app.retrieval.service import RetrievalRequest, RetrievalResult, RetrievalService

__all__ = ["RetrievalRequest", "RetrievalResult", "RetrievalService", "RetrievalUnavailable"]