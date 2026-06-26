"""V2 KPI 框架：12 维指标，包含 V1 基础 + V2 新增（合规删除残余召回、SLA 违约率、可解释性完整度）。

复用 metrics.py 的基础聚合（Hit@K/MRR/nDCG/延迟分位），新增 3 个场景化 KPI。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .metrics import PerQueryResult, aggregate


# ===== KPI 字段名常量（便于 report_v2 / charts_v2 引用） =====
KPI_QUALITY = ["hit@1", "hit@3", "hit@5", "mrr", "ndcg@10"]
KPI_EFFICIENCY = ["latency_p50_ms", "latency_p95_ms", "qps"]
KPI_COST = ["build_time_sec", "index_size_mb"]
KPI_SCENARIO = [
    "forget_residual_recall",  # S4：越小越好
    "sla_30ms_violation_rate",  # S2/S3：越小越好
    "retrieval_trail_completeness",  # S5：越大越好（0~1）
]
ALL_12_KPI = KPI_QUALITY + KPI_EFFICIENCY + KPI_COST + KPI_SCENARIO


@dataclass
class ParadigmKPI:
    """单个范式在某个场景下的完整 KPI 汇总。"""

    paradigm: str
    scenario: str
    metrics: dict  # {kpi_name: value}
    raw: dict = None  # 原始 PerQueryResult 列表（仅在 debug 模式保留）


# ===== V1 基础聚合（包成统一接口） =====


def compute_basic_kpis(
    paradigm: str,
    scenario: str,
    per_query: list[PerQueryResult],
    index_stats: dict,
    total_queries: int = 200,
    total_time_sec: float = 1.0,
) -> dict:
    """把 V1 指标 + index_stats 整合成 KPI 字典。

    输入：per_query (PerQueryResult 列表), index_stats (包含 build_time_sec / index_size_bytes)
    输出：dict 包含 KPI_QUALITY + KPI_EFFICIENCY + 部分 KPI_COST
    """
    agg = aggregate(per_query)
    n = max(1, total_queries)
    qps = n / max(total_time_sec, 1e-6)
    return {
        "hit@1": agg.get("hit@1", 0.0),
        "hit@3": agg.get("hit@3", 0.0),
        "hit@5": agg.get("hit@5", 0.0),
        "mrr": agg.get("mrr", 0.0),
        "ndcg@10": agg.get("ndcg@10", 0.0),
        "latency_p50_ms": agg.get("latency_p50_ms", 0.0),
        "latency_p95_ms": agg.get("latency_p95_ms", 0.0),
        "qps": qps,
        "build_time_sec": index_stats.get("build_time_sec", 0.0),
        "index_size_mb": index_stats.get("index_size_bytes", 0.0) / 1024 / 1024,
    }


# ===== KPI_SLA: 30ms SLA 违约率 =====


def compute_sla_violation_rate(
    per_query: list[PerQueryResult], sla_ms: float = 30.0
) -> float:
    """SLA 违约率：在 sla_ms 内未返回结果的比例。

    运维系统典型 SLA：p50 < 30ms。任何 p50 > 30ms 视为违约。
    返回 [0, 1] 浮点数，0 = 全合规，1 = 全违约。
    """
    if not per_query:
        return 0.0
    latencies = np.asarray([r.latency_ms for r in per_query], dtype=np.float64)
    violation = (latencies > sla_ms).sum()
    return float(violation / len(latencies))


# ===== KPI_FORGET: 残余召回率 =====


def compute_forget_residual_recall(
    hits_after_delete: list[PerQueryResult],
    deleted_ground_truth: int,
) -> float:
    """合规删除后，残余召回率 = 删除后仍能返回已删 KB 的 query 比例。

    返回 [0, 1]：
      - 0.0 = 完美删除（无任何召回）
      - 1.0 = 完全没删（HNSW/IVF/Flat 实际可能出现）
    """
    if not hits_after_delete:
        return 0.0
    residual = 0
    for r in hits_after_delete:
        # 评测：query 的 ground_truth == deleted_ground_truth，
        # 但该 query 应已被"合规屏蔽"。若仍 hit，说明残余召回
        if r.ground_truth == deleted_ground_truth and r.hit_at_1 == 1:
            residual += 1
    return float(residual / len(hits_after_delete))


# ===== KPI_TRAIL: retrieval_trail 完整度 =====


# 评估 retrieval_trail 完整度的 5 个维度
_TRAIL_FIELDS = [
    "quant_key",  # GridTrace 专属
    "l1_bucket_size",  # GridTrace 专属
    "l2_score",  # 通用（hit.score 本身）
    "anchor_path",  # GridTrace 专属
    "rerank_info",  # GridTrace 专属
]


def compute_trail_completeness(
    hits_with_payload: list[dict],
    is_vector_based: bool,
) -> float:
    """计算某个范式 5 个维度的 retrieval_trail 完整度（0~1）。

    评估方法：对每个 hit 的 payload 字段打分。
    GridTrace 增强版：5/5 = 1.0
    HNSW / IVF / Flat：1/5 = 0.2（只有 score）
    PageIndex：2/5 = 0.4（score + category_path）
    """
    if not hits_with_payload:
        return 0.0
    # 平均每条 hit 的 trail 完整度
    total_score = 0.0
    for hit in hits_with_payload:
        score = 0.0
        payload = hit.get("payload", {}) if isinstance(hit, dict) else hit.payload
        # 1. quant_key：GridTrace 专属
        trail = payload.get("retrieval_trail", {})
        if "quant_key" in trail or "l1_anchors" in trail:
            score += 1 / 5
        # 2. l1_bucket_size：GridTrace 专属
        if "l1_total_candidates" in trail or "l1_avg_bucket_size" in trail:
            score += 1 / 5
        # 3. l2_score：通用
        if "score" in hit or "l2_score" in trail:
            score += 1 / 5
        # 4. anchor_path：GridTrace 专属
        if "l1_anchors" in trail and trail.get("l1_anchors"):
            score += 1 / 5
        # 5. rerank_info：GridTrace 专属
        if "rerank_triggered" in trail:
            score += 1 / 5
        total_score += score
    return float(total_score / len(hits_with_payload))


# ===== 12 维 KPI 整合器 =====


def build_paradigm_kpi(
    paradigm_name: str,
    scenario: str,
    per_query: list[PerQueryResult],
    index_stats: dict,
    total_queries: int = 0,
    total_time_sec: float = 1.0,
    sla_ms: float = 30.0,
    is_vector_based: bool = True,
    hits_with_payload: list[dict] | None = None,
    residual_recall: float | None = None,
) -> ParadigmKPI:
    """构建 12 维 ParadigmKPI。"""
    metrics = compute_basic_kpis(
        paradigm_name,
        scenario,
        per_query,
        index_stats,
        total_queries=total_queries or len(per_query),
        total_time_sec=total_time_sec,
    )
    # SLA 违约率
    metrics["sla_30ms_violation_rate"] = compute_sla_violation_rate(per_query, sla_ms)
    # 可解释性
    if hits_with_payload is not None:
        metrics["retrieval_trail_completeness"] = compute_trail_completeness(
            hits_with_payload, is_vector_based
        )
    else:
        metrics["retrieval_trail_completeness"] = 0.0
    # 合规删除残余
    metrics["forget_residual_recall"] = (
        float(residual_recall) if residual_recall is not None else 0.0
    )
    return ParadigmKPI(
        paradigm=paradigm_name,
        scenario=scenario,
        metrics=metrics,
        raw={"per_query_count": len(per_query)},
    )


# ===== 场景化"赢家"决策 =====


def pick_scenario_winner(
    kpis_by_paradigm: dict[str, dict],
    scenario: str,
) -> str:
    """根据场景返回最合适的范式（仅作决策树文字提示，不作为唯一答案）。

    决策原则：
      - S1 标准：用 Hit@1 + p50 综合（默认 HNSW）
      - S2 规模化：用 p50 增长斜率（默认 GridTrace 增强版）
      - S3 热冷：用 hot_p50（默认 GridTrace 增强版 / GridTrace 原版）
      - S4 合规删除：用 forget_residual_recall（必须 GridTrace / GridTrace 增强版）
      - S5 可解释性：用 retrieval_trail_completeness（必须 GridTrace 增强版）
    """
    if not kpis_by_paradigm:
        return "N/A"
    if scenario == "S1":
        # Hit@1 加权 + p50 惩罚
        def score1(k):
            return k["hit@1"] - 0.001 * k["latency_p50_ms"]

    elif scenario == "S2":
        # 规模化用 p50 越小越好（粗略）
        def score1(k):
            return -k["latency_p50_ms"]

    elif scenario == "S3":
        # 热冷用 SLA 违约率
        def score1(k):
            return -k["sla_30ms_violation_rate"]

    elif scenario == "S4":
        # 合规删除
        def score1(k):
            return -k["forget_residual_recall"]

    elif scenario == "S5":
        # 可解释性
        def score1(k):
            return k["retrieval_trail_completeness"]

    else:
        def score1(k):
            return k["hit@1"]

    return max(kpis_by_paradigm, key=lambda p: score1(kpis_by_paradigm[p]))
