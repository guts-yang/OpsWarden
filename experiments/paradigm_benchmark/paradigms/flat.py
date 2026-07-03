"""Flat / Brute-Force Cosine Paradigm.

Computes cosine similarity against every entry in the KB.
O(N * d) per query, d=512. The accuracy upper bound for all ANN methods.
"""
from __future__ import annotations

import time

import numpy as np

from .base import Hit, IndexStats, Paradigm


class FlatParadigm(Paradigm):
    name = "Flat"

    def __init__(self) -> None:
        self._embeddings: np.ndarray | None = None  # (N, 512) float32
        self._page_indices: np.ndarray | None = None  # (N,) int32
        self._build_time = 0.0
        self._index_size = 0

    def build(self, entries: list[dict]) -> IndexStats:
        t0 = time.perf_counter()
        embs = np.asarray([e["embedding"] for e in entries], dtype=np.float32)
        # L2-normalize for cosine via dot product
        norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-12
        embs = embs / norms
        self._embeddings = embs
        self._page_indices = np.asarray([int(e["page_index"]) for e in entries], dtype=np.int32)
        self._build_time = time.perf_counter() - t0
        # Size = N * 512 * 4 bytes (float32)
        self._index_size = int(embs.nbytes)
        return IndexStats(
            build_time_sec=self._build_time,
            index_size_bytes=self._index_size,
            extra={"n_entries": int(embs.shape[0]), "dim": int(embs.shape[1])},
        )

    def search(self, query: str, query_embedding: list[float], top_k: int) -> list[Hit]:
        if self._embeddings is None or len(self._embeddings) == 0:
            return []
        q = np.asarray(query_embedding, dtype=np.float32)
        qn = float(np.linalg.norm(q)) + 1e-12
        q = q / qn
        # scores = q @ embs.T  (1, 512) @ (512, N) = (N,)
        scores = self._embeddings @ q
        # Top-K via argpartition for speed
        if top_k >= len(scores):
            top_idx = np.argsort(-scores)
        elif top_k == 0:
            return []
        else:
            cand = np.argpartition(-scores, top_k)[:top_k]
            top_idx = cand[np.argsort(-scores[cand])]
        hits: list[Hit] = []
        for idx in top_idx:
            hits.append(
                Hit(
                    page_index=int(self._page_indices[idx]),
                    score=float(scores[idx]),
                )
            )
        return hits

    def get_index_size_bytes(self) -> int:
        return self._index_size

    @property
    def is_vector_based(self) -> bool:
        return True
