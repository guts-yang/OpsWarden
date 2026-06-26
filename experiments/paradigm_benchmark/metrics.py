"""Evaluation metrics for RAG paradigm benchmark."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class PerQueryResult:
    query_id: int
    ground_truth: int
    hit_at_1: int  # 0/1
    hit_at_3: int  # 0/1
    hit_at_5: int  # 0/1
    hit_at_10: int  # 0/1
    reciprocal_rank: float  # 1/rank, 0 if not found
    latency_ms: float  # per-query wall-clock (median across repeats)
    ndcg_at_10: float


def hit_at_k(ranked_page_indices: list[int], ground_truth: int, k: int) -> int:
    return 1 if ground_truth in ranked_page_indices[:k] else 0


def reciprocal_rank(ranked_page_indices: list[int], ground_truth: int) -> float:
    for i, p in enumerate(ranked_page_indices, start=1):
        if p == ground_truth:
            return 1.0 / i
    return 0.0


def dcg_at_k(relevances: list[float], k: int) -> float:
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances[:k]))


def ndcg_at_k(ranked_page_indices: list[int], ground_truth: int, k: int) -> float:
    rels = [1.0 if p == ground_truth else 0.0 for p in ranked_page_indices[:k]]
    dcg = dcg_at_k(rels, k)
    # ideal: relevance of 1 at rank 1
    idcg = dcg_at_k([1.0], k)
    return dcg / idcg if idcg > 0 else 0.0


def aggregate(results: list[PerQueryResult]) -> dict:
    """Aggregate per-query results into paradigm-level metrics."""
    if not results:
        return {}
    arr = np.asarray(
        [
            [
                r.hit_at_1,
                r.hit_at_3,
                r.hit_at_5,
                r.hit_at_10,
                r.reciprocal_rank,
                r.ndcg_at_10,
            ]
            for r in results
        ],
        dtype=np.float64,
    )
    latencies = np.asarray([r.latency_ms for r in results], dtype=np.float64)
    return {
        "n_queries": len(results),
        "hit@1": float(arr[:, 0].mean()),
        "hit@3": float(arr[:, 1].mean()),
        "hit@5": float(arr[:, 2].mean()),
        "hit@10": float(arr[:, 3].mean()),
        "mrr": float(arr[:, 4].mean()),
        "ndcg@10": float(arr[:, 5].mean()),
        "latency_p50_ms": float(np.percentile(latencies, 50)),
        "latency_p95_ms": float(np.percentile(latencies, 95)),
        "latency_mean_ms": float(latencies.mean()),
        "latency_std_ms": float(latencies.std(ddof=1)) if len(latencies) > 1 else 0.0,
    }


def aggregate_topk_curve(
    results_by_topk: dict[int, list[PerQueryResult]],
) -> dict:
    """For Recall-Latency tradeoff: metrics as a function of top_k.

    results_by_topk: {top_k: [PerQueryResult]}
    Returns: {top_k: {hit@k, latency_mean_ms, ...}}
    """
    out = {}
    for k, results in sorted(results_by_topk.items()):
        out[int(k)] = aggregate(results)
    return out
