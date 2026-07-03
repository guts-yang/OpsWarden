"""V2 S4 合规精确删除测试。

逻辑：
  1. 在 N 条 KB 上跑 100 query 检索，记录正常召回率
  2. 选 1 条 KB（与 ≥3 条 query 关联）执行删除
  3. 重建索引（GridTrace 重建 quant_key 桶；HNSW 需重建；IVF/Flat 重建）
  4. 重新跑同样 100 query，统计"残余召回率"
     - 残余召回率 = 删除后仍能返回已删 KB 的 query 比例
     - 完美合规 = 0.0；HNSW/IVF/Flat 实际可能 5~15%（重建时通常已清，但某些实现残留）
"""
from __future__ import annotations

import copy
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

from .metrics import PerQueryResult
from .paradigms import Paradigm
from .paradigms.base import Hit

logger = logging.getLogger("forgetting_test")


def rebuild_index_without(
    paradigm: Paradigm,
    full_kb_rows: list[dict],
    deleted_page_index: int,
) -> Paradigm:
    """重建索引，排除已删 KB。"""
    pruned = [r for r in full_kb_rows if int(r["page_index"]) != deleted_page_index]
    # 重新构造 paradigm 实例（保证完全重建）
    new_p = paradigm.__class__(**{
        k: v for k, v in paradigm.__dict__.items()
        if k.startswith("_") is False and k not in {
            "_entries", "_anchors", "_index", "_build_time", "_index_size",
            "_coarse_anchors", "_coarse_key_to_idx", "_main_key_to_idx", "_categories",
            "_page_indices", "_embeddings", "_cluster_to_indices", "_centroids",
            "_bm25_question", "_category_texts", "_category_doc_lens", "_avg_doc_len",
        }
    })
    new_p.build(pruned)
    return new_p


def run_forgetting_test(
    paradigm: Paradigm,
    full_kb_rows: list[dict],
    queries: list[dict],
    deleted_page_index: int,
    top_k: int = 3,
    repeats: int = 3,
) -> dict:
    """对单个范式执行合规删除测试，返回 {residual_recall, before_hit, after_hit}。"""
    # 1. 删除前：跑 100 query
    before_hits: list[Hit] = []
    for q in queries:
        if isinstance(q, dict) and q.get("embedding"):
            qe = q["embedding"]
        else:
            from app.rag.embedder import embed_query
            qe = embed_query(q.get("query", ""))
        # warmup + measured
        for _ in range(2):
            paradigm.search(q.get("query", ""), qe, top_k)
        hs = paradigm.search(q.get("query", ""), qe, top_k)
        before_hits.extend(hs[:1])  # 取 top-1

    before_hit = sum(1 for h in before_hits if h.page_index == deleted_page_index)

    # 2. 重建（删除 1 条）
    logger.info("Rebuilding %s without page_index=%d ...", paradigm.name, deleted_page_index)
    new_p = rebuild_index_without(paradigm, full_kb_rows, deleted_page_index)

    # 3. 删除后：跑同样 100 query
    after_hits: list[Hit] = []
    for q in queries:
        if isinstance(q, dict) and q.get("embedding"):
            qe = q["embedding"]
        else:
            from app.rag.embedder import embed_query
            qe = embed_query(q.get("query", ""))
        hs = new_p.search(q.get("query", ""), qe, top_k)
        after_hits.extend(hs[:1])

    after_hit = sum(1 for h in after_hits if h.page_index == deleted_page_index)
    n_queries = len(queries)
    residual_recall = after_hit / max(n_queries, 1)

    return {
        "deleted_page_index": int(deleted_page_index),
        "before_hit": int(before_hit),
        "after_hit": int(after_hit),
        "n_queries": int(n_queries),
        "residual_recall": float(residual_recall),
        "rebuild_sec": 0.0,  # 重建耗时可在调用方用 build() 单独测
    }
