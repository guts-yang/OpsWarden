"""Unified RAG retrieval paradigm interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Hit:
    """A single retrieval hit returned by a paradigm."""

    page_index: int
    score: float
    payload: dict = field(default_factory=dict)


@dataclass
class IndexStats:
    """Index construction statistics for a paradigm."""

    build_time_sec: float
    index_size_bytes: int
    extra: dict = field(default_factory=dict)


class Paradigm(ABC):
    """Abstract base for all RAG paradigms.

    Lifecycle: build(entries) -> search(query, top_k) -> Hit[]
    """

    name: str = "abstract"

    @abstractmethod
    def build(self, entries: list[dict]) -> IndexStats:
        """Build the index from a list of entries.

        Each entry dict must contain:
            - id (int)
            - page_index (int)
            - question (str)
            - solution (str)
            - category (str)
            - embedding (list[float] of length 512)  -- already pre-computed
        """

    @abstractmethod
    def search(self, query: str, query_embedding: list[float], top_k: int) -> list[Hit]:
        """Search by both raw text and pre-computed embedding vector.

        The paradigm decides whether to use the text (PageIndex, BM25) or
        the vector (Flat, IVF, HNSW, GridTrace) or both.
        """

    @abstractmethod
    def get_index_size_bytes(self) -> int:
        """Return the persisted index size in bytes."""

    @property
    @abstractmethod
    def is_vector_based(self) -> bool:
        """True if the paradigm uses dense vector search."""
