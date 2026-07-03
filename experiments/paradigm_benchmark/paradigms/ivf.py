"""IVF (Inverted File) Paradigm.

In-memory IVF using sklearn KMeans for coarse quantization.
For each query, we search the n_probe nearest cluster centroids, then
brute-force cosine within the union of those clusters. This is the
algorithmic equivalent of pgvector's IVFFlat index used in the production
database.
"""
from __future__ import annotations

import time

import numpy as np
from sklearn.cluster import KMeans

from .base import Hit, IndexStats, Paradigm


class IVFParadigm(Paradigm):
    name = "IVF"

    def __init__(self, n_probe: int = 8) -> None:
        self.n_probe = n_probe
        self._embeddings: np.ndarray | None = None
        self._page_indices: np.ndarray | None = None
        self._cluster_to_indices: list[np.ndarray] = []
        self._centroids: np.ndarray | None = None
        self._build_time = 0.0
        self._index_size = 0

    def _choose_n_clusters(self, n: int) -> int:
        # Same heuristic as pgvector default: sqrt(N) rounded, capped
        return max(2, min(int(np.sqrt(n)), 256))

    def build(self, entries: list[dict]) -> IndexStats:
        t0 = time.perf_counter()
        embs = np.asarray([e["embedding"] for e in entries], dtype=np.float32)
        norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-12
        embs = embs / norms
        n = embs.shape[0]
        n_clusters = self._choose_n_clusters(n)
        # n_init=3 to keep build time reasonable on large N
        kmeans = KMeans(n_clusters=n_clusters, n_init=3, random_state=42, algorithm="lloyd")
        labels = kmeans.fit_predict(embs)
        # Inverted list: cluster_id -> member indices
        self._cluster_to_indices = [np.where(labels == c)[0] for c in range(n_clusters)]
        self._centroids = kmeans.cluster_centers_.astype(np.float32)
        # L2 normalize centroids
        cn = np.linalg.norm(self._centroids, axis=1, keepdims=True) + 1e-12
        self._centroids = self._centroids / cn
        self._embeddings = embs
        self._page_indices = np.asarray([int(e["page_index"]) for e in entries], dtype=np.int32)
        self._build_time = time.perf_counter() - t0
        # Size = embeddings + centroids
        self._index_size = int(embs.nbytes + self._centroids.nbytes)
        return IndexStats(
            build_time_sec=self._build_time,
            index_size_bytes=self._index_size,
            extra={"n_clusters": n_clusters, "n_probe": self.n_probe, "n_entries": n},
        )

    def search(self, query: str, query_embedding: list[float], top_k: int) -> list[Hit]:
        if self._embeddings is None or self._centroids is None:
            return []
        q = np.asarray(query_embedding, dtype=np.float32)
        qn = float(np.linalg.norm(q)) + 1e-12
        q = q / qn
        # L1: find top n_probe centroids by cosine
        centroid_scores = self._centroids @ q
        n_probe = min(self.n_probe, len(self._centroids))
        # If n_probe == 0 (degenerate), no candidates
        if n_probe == 0:
            return []
        # Use full sort when n_probe equals the number of centroids
        if n_probe >= len(self._centroids):
            top_clusters = np.argsort(-centroid_scores)
        else:
            top_clusters = np.argpartition(-centroid_scores, n_probe)[:n_probe]
        # L2: brute-force within union of probed clusters
        candidate_idx: set[int] = set()
        for c in top_clusters:
            candidate_idx.update(self._cluster_to_indices[int(c)].tolist())
        if not candidate_idx:
            return []
        cand_arr = np.fromiter(candidate_idx, dtype=np.int64)
        cand_embs = self._embeddings[cand_arr]
        cand_scores = cand_embs @ q
        # Top-K
        if top_k >= len(cand_arr):
            order = np.argsort(-cand_scores)
        else:
            top = np.argpartition(-cand_scores, top_k)[:top_k]
            order = top[np.argsort(-cand_scores[top])]
        hits: list[Hit] = []
        for i in order:
            gi = int(cand_arr[i])
            hits.append(
                Hit(
                    page_index=int(self._page_indices[gi]),
                    score=float(cand_scores[i]),
                )
            )
        return hits

    def get_index_size_bytes(self) -> int:
        return self._index_size

    @property
    def is_vector_based(self) -> bool:
        return True
