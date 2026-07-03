"""GridTrace Paradigm.

Reuses the existing two-stage retrieval logic in
backend/app/rag/eval_engine.py: L1 anchor cosine (over quantized vectors)
-> L2 entry cosine (exact re-ranking). This is the production GridTrace
implementation, not a new simulation.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

# Make backend importable
ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.rag.eval_engine import (  # noqa: E402
    AnchorBucket,
    EvalEntry,
    build_anchors,
    search_inmemory,
)
from app.rag.quantizer import quantize_vector  # noqa: E402

from .base import Hit, IndexStats, Paradigm


class GridTraceParadigm(Paradigm):
    name = "GridTrace"

    def __init__(self, epsilon: float = 0.02, anchor_k: int = 8, threshold: float = 0.65) -> None:
        self.epsilon = epsilon
        self.anchor_k = anchor_k
        self.threshold = threshold
        self._entries: list[EvalEntry] = []
        self._anchors: list[AnchorBucket] = []
        self._build_time = 0.0
        self._index_size = 0

    def build(self, entries: list[dict]) -> IndexStats:
        t0 = time.perf_counter()
        self._entries = [
            EvalEntry(
                page_index=int(e["page_index"]),
                question=str(e["question"]),
                solution=str(e["solution"]),
                category=str(e.get("category", "")),
                embedding=np.asarray(e["embedding"], dtype=np.float64),
            )
            for e in entries
        ]
        self._anchors = build_anchors(self._entries, self.epsilon)
        self._build_time = time.perf_counter() - t0
        # Size = (N + N_anchors) * dim * 8 bytes (float64); dim 随 embedding 模型自适应
        _emb_dim = self._entries[0].embedding.shape[0] if self._entries else 512
        self._index_size = (len(self._entries) + len(self._anchors)) * _emb_dim * 8
        return IndexStats(
            build_time_sec=self._build_time,
            index_size_bytes=self._index_size,
            extra={
                "n_entries": len(self._entries),
                "n_anchors": len(self._anchors),
                "epsilon": self.epsilon,
                "anchor_k": self.anchor_k,
            },
        )

    def search(self, query: str, query_embedding: list[float], top_k: int) -> list[Hit]:
        if not self._entries or not self._anchors:
            return []
        qvec = np.asarray(query_embedding, dtype=np.float64)
        hits, _ = search_inmemory(
            qvec,
            self._entries,
            self._anchors,
            anchor_k=self.anchor_k,
            threshold=self.threshold,
            top_k=top_k,
        )
        return [
            Hit(
                page_index=int(h["page_index"]),
                score=float(h["score"]),
                payload={"question": h["question"], "solution": h["solution"], "category": h["category"]},
            )
            for h in hits
        ]

    def get_index_size_bytes(self) -> int:
        return self._index_size

    @property
    def is_vector_based(self) -> bool:
        return True
