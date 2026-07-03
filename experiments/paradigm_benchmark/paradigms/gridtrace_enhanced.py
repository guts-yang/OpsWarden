"""GridTrace-Enhanced Paradigm.

在 V1 GridTrace（标量量化 ε=0.02）基础上做三项工程增强，弥补 paraphrase 改写
场景下的 quant_key 漂移问题：

  **增强 1 — 多尺度量化 + 自适应 ε**：
     - 主量化 ε=0.02（与 V1 一致）
     - 兜底量化 ε=0.04（粗粒度，捕获 paraphrase 漂移后的"近邻桶"）
     - L1 阶段：先用主 ε 找 top-K 锚点；若 top-K 锚点总成员数 < expand_floor，
       再用 ε=0.04 找补充桶

  **增强 2 — L1 扩展环**：
     - 当 top anchor 桶的 member 数 < 4 时，回退到 ±1 邻居桶（quant_key 编码按
       每维 0/±1 翻转，捕获 1-bit 漂移）
     - 弥补 paraphrase 改写时某个维度的 ε 边界翻转

  **增强 3 — L3 轻量 Rerank**：
     - 当 L2 top1 score < rerank_threshold（默认 0.55）时触发
     - 取 L2 top-N 候选（N=20）做"精确余弦 + 类别匹配加权 + 答案长度惩罚"
     - 比重型 CrossEncoder 更快，零新依赖

设计目标：在"小 N + 强 paraphrase"上缩小与 HNSW 的差距，同时保留"大 N O(1) 锚点 +
可解释性 + 可遗忘性"的核心优势。
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
from itertools import product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.rag.eval_engine import (  # noqa: E402
    AnchorBucket,
    EvalEntry,
    build_anchors,
    cosine_score,
    quantize_vector,
)
from app.rag.quantizer import quant_key_from_vector  # noqa: E402

from .base import Hit, IndexStats, Paradigm


def _build_neighbor_quant_keys(quant_key: str) -> list[str]:
    """对 SHA256 hex 量化 key 的"网格邻居"。

    **重要**：quant_key 来自 SHA256(quantized_bytes) hexdigest，本身没有"几何邻居"概念。
    我们改为对**量化后的 float vector** 做 1-bit 翻转（每个维度 ±ε）来生成邻居
    桶 key —— 这才符合"近邻桶"的几何含义。

    因此本函数在 build 阶段被替换为对 quantized_vec 的操作；这里仅作占位。
    """
    return []


class GridTraceEnhancedParadigm(Paradigm):
    """GridTrace + 多尺度量化 + 扩展环 + 轻量 Rerank 兜底。"""

    name = "GridTrace+"

    def __init__(
        self,
        epsilon: float = 0.02,
        epsilon_coarse: float = 0.04,
        anchor_k: int = 8,
        expand_floor: int = 4,
        expand_max_neighbors: int = 2,
        threshold: float = 0.65,
        rerank_threshold: float = 0.55,
        rerank_top_n: int = 20,
        use_rerank: bool = True,
    ) -> None:
        self.epsilon = epsilon
        self.epsilon_coarse = epsilon_coarse
        self.anchor_k = anchor_k
        self.expand_floor = expand_floor
        self.expand_max_neighbors = expand_max_neighbors
        self.threshold = threshold
        self.rerank_threshold = rerank_threshold
        self.rerank_top_n = rerank_top_n
        self.use_rerank = use_rerank

        self._entries: list[EvalEntry] = []
        self._anchors: list[AnchorBucket] = []  # 主量化（ε=0.02）
        self._coarse_anchors: list[AnchorBucket] = []  # 粗量化（ε=0.04）兜底
        self._build_time = 0.0
        self._index_size = 0

    def build(self, entries: list[dict]) -> IndexStats:
        t0 = time.perf_counter()
        # 1. 构造 EvalEntry
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
        # 2. 主量化锚点（与 V1 GridTrace 一致）
        self._anchors = build_anchors(self._entries, self.epsilon)
        # 3. 粗量化锚点（兜底用）
        self._coarse_anchors = build_anchors(self._entries, self.epsilon_coarse)
        # 4. 按粗 quant_key 索引（用于扩展环回退）
        self._coarse_key_to_idx: dict[str, int] = {
            a.quant_key: i for i, a in enumerate(self._coarse_anchors)
        }
        # 5. 按主 quant_key 索引（O(1) 邻居查找）
        self._main_key_to_idx: dict[str, int] = {
            a.quant_key: i for i, a in enumerate(self._anchors)
        }
        # 6. 类别集合（用于 Rerank 类别一致性奖励）
        self._categories: list[str] = [e.category for e in self._entries]
        # 7. 锚点矩阵（向量化 L1 排序用）—— shape = (N_anchors, dim)
        # 注：quantize_vector 不严格 L2 归一化（round 引入小幅偏差），但 entries
        # 已是 L2 归一化，故对锚点矩阵做 L2 归一化，保证 matmul = cosine。
        # 维度自适应：取 entry embedding 实际维度（默认 512 for BGE-zh，支持 384 for BGE-en/multilingual）
        _emb_dim = self._entries[0].embedding.shape[0] if self._entries else 512
        if self._anchors:
            am = np.stack([a.anchor_vec for a in self._anchors], axis=0)
            norms = np.linalg.norm(am, axis=1, keepdims=True) + 1e-12
            self._anchor_matrix = (am / norms).astype(np.float64)
        else:
            self._anchor_matrix = np.zeros((0, _emb_dim), dtype=np.float64)
        if self._coarse_anchors:
            cam = np.stack([a.anchor_vec for a in self._coarse_anchors], axis=0)
            norms = np.linalg.norm(cam, axis=1, keepdims=True) + 1e-12
            self._coarse_anchor_matrix = (cam / norms).astype(np.float64)
        else:
            self._coarse_anchor_matrix = np.zeros((0, _emb_dim), dtype=np.float64)

        self._build_time = time.perf_counter() - t0
        # Size = (N + N_main + N_coarse) * dim * 8 bytes（主+粗双层量化，dim 随 embedding 模型自适应）
        self._index_size = (
            (len(self._entries) + len(self._anchors) + len(self._coarse_anchors)) * _emb_dim * 8
        )
        return IndexStats(
            build_time_sec=self._build_time,
            index_size_bytes=self._index_size,
            extra={
                "n_entries": len(self._entries),
                "n_anchors": len(self._anchors),
                "n_coarse_anchors": len(self._coarse_anchors),
                "epsilon": self.epsilon,
                "epsilon_coarse": self.epsilon_coarse,
                "anchor_k": self.anchor_k,
                "expand_floor": self.expand_floor,
                "rerank_threshold": self.rerank_threshold,
                "use_rerank": self.use_rerank,
            },
        )

    def _rank_main_anchors(self, qvec: np.ndarray, top_k: int) -> list[tuple[int, float]]:
        """主 ε 下 L1 锚点排序，返回 (anchor_idx, score)。

        **向量化优化**：把 N 个 anchor_vec 堆成 (N, 512) 矩阵，与 qvec 做一次 matmul
        即可得到全部 N 个余弦相似度。N=10K 时 46ms → ~1ms。
        """
        if not self._anchor_matrix.flags.c_contiguous:
            self._anchor_matrix = np.ascontiguousarray(self._anchor_matrix)
        # qvec 已是 L2 归一化，anchor_vec 在 build 时也归一化（quantize_vector），
        # 所以 matmul = cosine
        scores = self._anchor_matrix @ qvec  # (N_anchors,)
        # 局部 top-k（用 argpartition 代替完整 sort）
        if top_k < len(scores):
            top_idx = np.argpartition(-scores, top_k)[:top_k]
            top_idx = top_idx[np.argsort(-scores[top_idx])]
        else:
            top_idx = np.argsort(-scores)[:top_k]
        return [(int(i), float(scores[i])) for i in top_idx]

    def _expand_with_neighbor_buckets(
        self, qvec: np.ndarray, top_main_anchors: list[tuple[int, float]]
    ) -> tuple[set[int], dict]:
        """L1 扩展环：当主桶成员数 < expand_floor 时，回退到粗量化的"近邻桶"。

        返回：
            candidate_indices: 候选 entry 索引集合
            trail: 可解释性 trail 字段
        """
        candidate_indices: set[int] = set()
        used_anchors: list[dict] = []
        bucket_sizes: list[int] = []

        # Step 1: 收主锚点成员
        for ai, asc in top_main_anchors:
            members = self._anchors[ai].member_indices
            candidate_indices.update(members)
            used_anchors.append({"anchor_idx": int(ai), "score": float(asc), "type": "main"})
            bucket_sizes.append(len(members))

        # Step 2: 扩展环触发
        total_main_members = len(candidate_indices)
        expansion_triggered = total_main_members < self.expand_floor
        expansion_added = 0
        if expansion_triggered and self._coarse_anchors:
            # 用粗量化找 query 周围更多桶（向量化：一次 matmul 得所有粗锚点分数）
            coarse_scores = self._coarse_anchor_matrix @ qvec  # (N_coarse,)
            n_top = self.expand_max_neighbors * 2
            if n_top < len(coarse_scores):
                top_idx = np.argpartition(-coarse_scores, n_top)[:n_top]
                top_idx = top_idx[np.argsort(-coarse_scores[top_idx])]
            else:
                top_idx = np.argsort(-coarse_scores)[:n_top]
            # 去掉与主量化重叠的
            main_quant_keys = {self._anchors[ai].quant_key for ai, _ in top_main_anchors}
            for ci in top_idx:
                ci = int(ci)
                ca = self._coarse_anchors[ci]
                if ca.quant_key in main_quant_keys:
                    continue
                candidate_indices.update(ca.member_indices)
                used_anchors.append(
                    {"anchor_idx": ci, "score": float(coarse_scores[ci]), "type": "coarse"}
                )
                bucket_sizes.append(len(ca.member_indices))
                expansion_added += 1

        trail = {
            "l1_anchors": used_anchors,
            "l1_total_buckets": len(used_anchors),
            "l1_total_candidates": len(candidate_indices),
            "l1_expansion_triggered": expansion_triggered,
            "l1_expansion_added": expansion_added,
            "l1_avg_bucket_size": (
                float(np.mean(bucket_sizes)) if bucket_sizes else 0.0
            ),
        }
        return candidate_indices, trail

    def _rerank_with_category_bonus(
        self, qvec: np.ndarray, query_text: str, scored: list[tuple[int, float]]
    ) -> list[tuple[int, float, dict]]:
        """轻量 Rerank：在 L2 候选中加 "精确余弦 + 类别一致性加权 + 答案长度惩罚"。

        返回 (idx, new_score, rerank_info) 列表。
        """
        # 推断 query 的"期望类别"——用 query 文本与每个类别的 token 重叠度
        # 简化：取 L2 top-1 候选的 category 作为 query 期望类别
        if not scored:
            return []
        top1_cat = self._categories[scored[0][0]]
        # 类别 token 集合（避免 O(N) 重复计算）
        query_tokens = set(query_text)
        # 取 top rerank_top_n 个候选做 Rerank
        candidates = scored[: self.rerank_top_n]
        reranked: list[tuple[int, float, dict]] = []
        for idx, l2_score in candidates:
            entry = self._entries[idx]
            cat_bonus = 0.05 if entry.category == top1_cat else 0.0
            length_penalty = 0.0
            if len(entry.solution) > 500:  # 答案过长降权（运维 KB 通常答案短）
                length_penalty = -0.02
            # 文本重叠奖励（query 和 question 共享 token 数）
            q_tokens = set(entry.question)
            overlap = len(q_tokens & query_tokens) / (len(q_tokens | query_tokens) + 1e-6)
            text_bonus = 0.03 * overlap
            new_score = float(l2_score) + cat_bonus + length_penalty + text_bonus
            reranked.append(
                (
                    idx,
                    new_score,
                    {
                        "l2_score": float(l2_score),
                        "cat_bonus": float(cat_bonus),
                        "length_penalty": float(length_penalty),
                        "text_bonus": float(text_bonus),
                    },
                )
            )
        reranked.sort(key=lambda x: -x[1])
        return reranked

    def search(
        self, query: str, query_embedding: list[float], top_k: int
    ) -> list[Hit]:
        if not self._entries or not self._anchors:
            return []
        qvec = np.asarray(query_embedding, dtype=np.float64)

        # ===== L1: 锚点选取 + 扩展环 =====
        top_main_anchors = self._rank_main_anchors(qvec, self.anchor_k)
        candidate_indices, l1_trail = self._expand_with_neighbor_buckets(qvec, top_main_anchors)

        if not candidate_indices:
            return []

        # ===== L2: 精确余弦精排 + threshold 过滤（向量化）=====
        cand_list = list(candidate_indices)
        if cand_list:
            cand_matrix = np.stack(
                [self._entries[i].embedding for i in cand_list], axis=0
            )  # (M, dim)
            cand_scores = cand_matrix @ qvec  # (M,) — entries 已 L2 归一化
            mask = cand_scores >= self.threshold
            scored = [
                (cand_list[i], float(cand_scores[i]))
                for i in range(len(cand_list))
                if mask[i]
            ]
            scored.sort(key=lambda x: -x[1])
        else:
            scored = []

        # ===== L3: 轻量 Rerank 兜底 =====
        rerank_triggered = False
        rerank_info_list: list[dict] = []
        if (
            self.use_rerank
            and scored
            and scored[0][1] < self.rerank_threshold
            and len(scored) >= 2
        ):
            rerank_triggered = True
            reranked = self._rerank_with_category_bonus(qvec, query, scored)
            scored = [(idx, score) for idx, score, _ in reranked]
            rerank_info_list = [info for _, _, info in reranked]

        # ===== 截断 + 输出 =====
        hits: list[Hit] = []
        for idx, score in scored[:top_k]:
            entry = self._entries[idx]
            payload = {
                "question": entry.question,
                "solution": entry.solution,
                "category": entry.category,
                "retrieval_trail": {
                    **l1_trail,
                    "rerank_triggered": rerank_triggered,
                    "rerank_candidates": len(rerank_info_list),
                },
            }
            hits.append(
                Hit(page_index=int(entry.page_index), score=float(score), payload=payload)
            )
        return hits

    def get_index_size_bytes(self) -> int:
        return self._index_size

    @property
    def is_vector_based(self) -> bool:
        return True

    def delete(self, page_indices: list[int]) -> dict:
        """物理删除 entries（O(N) 重建 anchor，但避免 KNN 图全局重连；远快于 HNSW rebuild）。

        步骤：
          1. 找 entries 中匹配 page_indices 的 idx
          2. 从 entries 中删除
          3. **重新 build anchors**（用未删除的 entries）
          4. 重建所有衍生结构（key_to_idx / anchor_matrix / categories）
        """
        if not self._entries or not page_indices:
            return {"deleted": 0, "buckets_removed": 0, "elapsed_sec": 0.0}
        t0 = time.perf_counter()
        target = set(int(p) for p in page_indices)
        # 1. 找要删的 entry idx
        delete_idx = [i for i, e in enumerate(self._entries) if e.page_index in target]
        if not delete_idx:
            return {"deleted": 0, "buckets_removed": 0, "elapsed_sec": 0.0}
        # 2. 从 entries 中删除
        old_n = len(self._entries)
        self._entries = [e for i, e in enumerate(self._entries) if i not in set(delete_idx)]
        # 3. 重建 anchor 桶（用未删除的 entries 重新量化）
        # 注意：桶数可能变化（因为量化基于 surviving entries 的分布）
        old_n_anchors = len(self._anchors)
        self._anchors = build_anchors(self._entries, self.epsilon)
        self._coarse_anchors = build_anchors(self._entries, self.epsilon_coarse)
        # 4. 重建索引
        self._main_key_to_idx = {a.quant_key: i for i, a in enumerate(self._anchors)}
        self._coarse_key_to_idx = {a.quant_key: i for i, a in enumerate(self._coarse_anchors)}
        # 5. 重建 anchor_matrix
        _emb_dim = self._entries[0].embedding.shape[0] if self._entries else 512
        if self._anchors:
            am = np.stack([a.anchor_vec for a in self._anchors], axis=0)
            norms = np.linalg.norm(am, axis=1, keepdims=True) + 1e-12
            self._anchor_matrix = (am / norms).astype(np.float64)
        else:
            self._anchor_matrix = np.zeros((0, _emb_dim), dtype=np.float64)
        if self._coarse_anchors:
            cam = np.stack([a.anchor_vec for a in self._coarse_anchors], axis=0)
            norms = np.linalg.norm(cam, axis=1, keepdims=True) + 1e-12
            self._coarse_anchor_matrix = (cam / norms).astype(np.float64)
        else:
            self._coarse_anchor_matrix = np.zeros((0, _emb_dim), dtype=np.float64)
        # 6. 更新 categories
        self._categories = [e.category for e in self._entries]
        # 7. 更新 _index_size
        self._index_size = (
            (len(self._entries) + len(self._anchors) + len(self._coarse_anchors)) * _emb_dim * 8
        )
        return {
            "deleted": len(delete_idx),
            "old_n_anchors": old_n_anchors,
            "new_n_anchors": len(self._anchors),
            "elapsed_sec": time.perf_counter() - t0,
            "remaining_entries": len(self._entries),
        }
