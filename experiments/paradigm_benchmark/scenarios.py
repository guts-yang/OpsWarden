"""V2 场景化评测定义：5 个真实运维场景。

每个场景是一个独立函数 `setup(kb_source, queries, ...) -> (entries, scenario_queries, kpi_evaluator)`，
由 `runner_v2.py` 统一调用。

场景列表：
  - S1 标准企业运维 FAQ
  - S2 规模化压力（N=1K/5K/10K/50K）
  - S3 热冷分布（N=10K，模拟 20% 热点 80% 长尾）
  - S4 合规精确删除
  - S5 可解释性（retrieval_trail 完整度）
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

logger = logging.getLogger("scenarios")


@dataclass
class ScenarioSpec:
    """单个场景的完整定义。"""

    id: str  # e.g. "S1"
    name: str  # 中文名
    description: str  # 1-2 句话场景描述
    kb_source: str  # KB 数据来源（json 路径或 size tag like "v3_1K"）
    query_filter: str  # "all" / "exact" / "paraphrase" / "hot" / "cold" / "negative" / "hard_confusion"
    extra: dict = field(default_factory=dict)  # 场景特有参数


# ===== S1 标准企业运维 FAQ =====
S1 = ScenarioSpec(
    id="S1",
    name="标准企业运维 FAQ",
    description=(
        "原始 400 条真实运维 KB，680 条查询（100 exact + 400 paraphrase + 100 negative + 80 hard_confusion）。"
        "作为基线场景，用于评估各范式在标准企业运维 FAQ 检索中的综合表现。"
    ),
    kb_source="v3",
    query_filter="all",
    extra={"hotspot_top_k": None},
)

# ===== S2 规模化压力 =====
S2 = ScenarioSpec(
    id="S2",
    name="规模化压力",
    description=(
        "N ∈ {1K, 5K, 10K, 50K} 四档规模，每档跑 100 条 paraphrase query。"
        "用于评估各范式在 KB 规模增长下的延迟、召回与可扩展性。"
    ),
    kb_source="multi_size",  # runner 会按 extra.sizes 循环
    query_filter="paraphrase",
    extra={"sizes": [1000, 5000, 10000, 50000], "n_queries_per_size": 100},
)

# ===== S3 热冷分布 =====
S3 = ScenarioSpec(
    id="S3",
    name="热冷分布（20% 热点 80% 长尾）",
    description=(
        "N=10K 真实扩展 KB。模拟运维真实访问：80% 查询来自 20% 高频 KB（热点），20% 来自长尾。"
        "GridTrace L1 锚点天然聚合热点 → 热点查询的 L1 候选集应 < 5 条，p50 应显著低于平均。"
    ),
    kb_source="v3_10K",
    query_filter="hot_cold",
    extra={"hot_frac_kb": 0.2, "hot_frac_queries": 0.8, "n_queries": 200},
)

# ===== S4 合规精确删除 =====
S4 = ScenarioSpec(
    id="S4",
    name="合规精确删除（GDPR / 审计）",
    description=(
        "随机选 1 条高频 KB（与 ≥3 条 query 关联）执行删除操作，再跑 100 query 重新检索。"
        "GridTrace 删 quant_key 桶后立即生效；HNSW 删节点 mark_deleted（实际仍可能召回）。"
        "关键指标：残余召回率（residual recall）越低越好。"
    ),
    kb_source="v3",
    query_filter="forget",
    extra={"n_test_queries": 100, "n_delete": 1},
)

# ===== S5 可解释性 =====
S5 = ScenarioSpec(
    id="S5",
    name="可解释性（retrieval_trail 完整度）",
    description=(
        "各范式返回结果时附带 retrieval_trail 字段。"
        "GridTrace 唯一能返回 {quant_key, l1_bucket_size, l2_score, anchor_path, rerank_info} 完整 trail。"
        "关键指标：retrieval_trail_completeness（0~1，越大越好）。"
    ),
    kb_source="v3",
    query_filter="paraphrase",
    extra={"n_queries": 50},
)


ALL_SCENARIOS: dict[str, ScenarioSpec] = {s.id: s for s in [S1, S2, S3, S4, S5]}


# ===== 场景查询过滤器 =====


def filter_queries(queries: list[dict], filter_mode: str) -> list[dict]:
    """根据 filter_mode 过滤查询。"""
    if filter_mode == "all":
        return queries
    if filter_mode == "paraphrase":
        return [q for q in queries if q.get("split") == "paraphrase"]
    if filter_mode == "exact":
        return [q for q in queries if q.get("split") == "exact"]
    if filter_mode == "negative":
        return [q for q in queries if q.get("split") == "negative"]
    if filter_mode == "hard_confusion":
        return [q for q in queries if q.get("split") == "hard_confusion"]
    return queries


def build_hot_cold_queries(
    queries: list[dict],
    kb_rows: list[dict],
    n_queries: int,
    hot_frac_kb: float,
    hot_frac_queries: float,
    seed: int = 42,
) -> list[dict]:
    """构造热冷分布查询集。

    1. 找 KB 中"被 query 命中次数最多"的 top hot_frac_kb 比例的 KB 当作"热点 KB"
    2. 80% 查询来自热点 KB（hot），20% 来自其余 KB（cold）
    """
    rng = np.random.default_rng(seed)
    # 统计每个 KB 的 query 命中数
    from collections import Counter

    page_query_count = Counter(q["page_index"] for q in queries if q.get("page_index") is not None)
    n_hot_kb = max(1, int(hot_frac_kb * len(kb_rows)))
    hot_kb_ids = {pid for pid, _ in page_query_count.most_common(n_hot_kb)}
    if not hot_kb_ids:
        hot_kb_ids = {kb_rows[i]["page_index"] for i in range(n_hot_kb)}

    hot_queries = [q for q in queries if q.get("page_index") in hot_kb_ids]
    cold_queries = [q for q in queries if q.get("page_index") not in hot_kb_ids]
    n_hot = int(hot_frac_queries * n_queries)
    n_cold = n_queries - n_hot
    sampled_hot = [hot_queries[i % len(hot_queries)] for i in range(n_hot)] if hot_queries else []
    sampled_cold = [cold_queries[i % len(cold_queries)] for i in range(n_cold)] if cold_queries else []
    mixed = sampled_hot + sampled_cold
    rng.shuffle(mixed)
    return mixed


def select_forget_target(kb_rows: list[dict], queries: list[dict]) -> dict:
    """选择 1 条高频 KB 作为删除目标（与 ≥3 条 query 关联）。"""
    from collections import Counter

    page_query_count = Counter(q["page_index"] for q in queries if q.get("page_index") is not None)
    # 找 page_index 在 KB 中且 query 数 ≥ 3 的最高频条目
    candidates = [
        (pid, cnt) for pid, cnt in page_query_count.items() if cnt >= 3
    ]
    candidates.sort(key=lambda x: -x[1])
    if not candidates:
        candidates = [(kb_rows[0]["page_index"], 1)]
    pid, cnt = candidates[0]
    target = next((r for r in kb_rows if r["page_index"] == pid), None)
    if not target:
        target = {"page_index": pid, "category": "", "question": "", "solution": ""}
    target = dict(target)
    target["_related_query_count"] = cnt
    target["_related_queries"] = [q for q in queries if q.get("page_index") == pid][:5]
    return target
