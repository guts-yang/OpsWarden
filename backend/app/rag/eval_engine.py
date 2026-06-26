"""In-memory RAG evaluation engine mirroring production two-stage retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.rag.quantizer import quant_key_from_vector, quantize_vector


@dataclass
class EvalEntry:
    page_index: int
    question: str
    solution: str
    category: str
    embedding: np.ndarray
    anchor_key: str | None = None


@dataclass
class AnchorBucket:
    quant_key: str
    anchor_vec: np.ndarray
    member_indices: list[int] = field(default_factory=list)


def compute_joint_embedding(qv: np.ndarray, sv: np.ndarray) -> np.ndarray:
    """Mirror ingest_kb_entry joint vector: (qv + sv) / 2 then L2-normalize."""
    joint = (qv + sv) / 2.0
    norm = float(np.linalg.norm(joint)) + 1e-12
    return (joint / norm).astype(np.float64)


def cosine_score(q: np.ndarray, v: np.ndarray) -> float:
    qn = float(np.linalg.norm(q)) + 1e-12
    vn = float(np.linalg.norm(v)) + 1e-12
    return float(np.dot(q, v) / (qn * vn))


def build_anchors(entries: list[EvalEntry], epsilon: float) -> list[AnchorBucket]:
    """Quantize entry embeddings into anchor buckets (in-memory upsert)."""
    buckets: dict[str, AnchorBucket] = {}
    for idx, entry in enumerate(entries):
        quantized = quantize_vector(entry.embedding.tolist(), epsilon)
        qk = quant_key_from_vector(quantized)
        entry.anchor_key = qk
        if qk not in buckets:
            buckets[qk] = AnchorBucket(quant_key=qk, anchor_vec=quantized)
        buckets[qk].member_indices.append(idx)
    return list(buckets.values())


def search_inmemory(
    qvec: np.ndarray,
    entries: list[EvalEntry],
    anchors: list[AnchorBucket],
    *,
    anchor_k: int,
    threshold: float,
    top_k: int,
) -> tuple[list[dict], list[int]]:
    """Two-stage search; returns (ranked hits, top anchor indices by L1 score).

    **向量化实现**：把 N 个 anchor_vec / entry.embedding 堆成矩阵，一次 matmul
    得到所有余弦相似度。N=10K 时 L1 由 46ms 降至 ~1ms。
    """
    q = np.asarray(qvec, dtype=np.float64)
    if not anchors:
        return [], []

    # ===== L1: 锚点余弦（向量化）=====
    anchor_matrix = np.stack([a.anchor_vec for a in anchors], axis=0)  # (N_anchors, dim)
    # 归一化（quantize_vector 的 round 不严格 L2 归一化）
    anchor_norms = np.linalg.norm(anchor_matrix, axis=1, keepdims=True) + 1e-12
    anchor_matrix = anchor_matrix / anchor_norms
    anchor_scores = anchor_matrix @ q  # (N_anchors,)
    if anchor_k < len(anchor_scores):
        top_idx = np.argpartition(-anchor_scores, anchor_k)[:anchor_k]
        top_idx = top_idx[np.argsort(-anchor_scores[top_idx])]
    else:
        top_idx = np.argsort(-anchor_scores)[:anchor_k]
    top_anchor_indices = [int(i) for i in top_idx]

    # 收集候选 entry
    candidate_indices: set[int] = set()
    for ai in top_anchor_indices:
        candidate_indices.update(anchors[ai].member_indices)

    # ===== L2: 候选精确余弦（向量化）=====
    cand_list = list(candidate_indices)
    if cand_list:
        cand_matrix = np.stack([entries[i].embedding for i in cand_list], axis=0)
        cand_scores = cand_matrix @ q
        scored = [
            (cand_list[i], float(cand_scores[i]))
            for i in range(len(cand_list))
            if cand_scores[i] >= threshold
        ]
        scored.sort(key=lambda x: -x[1])
    else:
        scored = []

    hits: list[dict] = []
    for idx, score in scored[:top_k]:
        entry = entries[idx]
        hits.append(
            {
                "page_index": entry.page_index,
                "question": entry.question,
                "solution": entry.solution,
                "category": entry.category,
                "score": round(score, 4),
            }
        )
    return hits, top_anchor_indices


def rank_all_candidates(
    qvec: np.ndarray,
    entries: list[EvalEntry],
    anchors: list[AnchorBucket],
    *,
    anchor_k: int,
) -> tuple[list[tuple[int, float]], list[int]]:
    """L2 ranking without threshold filter (for Hit@1 without threshold)."""
    q = np.asarray(qvec, dtype=np.float64)
    if not anchors:
        return [], []

    anchor_ranked = sorted(
        ((i, cosine_score(q, a.anchor_vec)) for i, a in enumerate(anchors)),
        key=lambda x: -x[1],
    )
    top_anchor_indices = [i for i, _ in anchor_ranked[:anchor_k]]

    candidate_indices: set[int] = set()
    for ai in top_anchor_indices:
        candidate_indices.update(anchors[ai].member_indices)

    scored = [(idx, cosine_score(q, entries[idx].embedding)) for idx in candidate_indices]
    scored.sort(key=lambda x: -x[1])
    return scored, top_anchor_indices


def l1_anchor_hit(
    entries: list[EvalEntry],
    anchors: list[AnchorBucket],
    expected_page_index: int,
    top_anchor_indices: list[int],
) -> bool:
    """True if any entry for expected_page_index has its anchor in L1 top anchors."""
    expected_keys = {
        e.anchor_key for e in entries
        if e.page_index == expected_page_index and e.anchor_key is not None
    }
    if not expected_keys:
        return False
    top_keys = {anchors[ai].quant_key for ai in top_anchor_indices}
    return bool(expected_keys & top_keys)
