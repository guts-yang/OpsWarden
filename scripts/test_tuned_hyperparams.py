#!/usr/bin/env python3
"""Validate that the tuned RAG hyperparameters are correctly applied to the backend.

This exercises the *real* production code path (`app.rag.retriever.search`) against
the live PostgreSQL + pgvector knowledge base. Only the embedding model is stubbed:
instead of downloading BAAI/bge-small-zh-v1.5, we reuse vectors already stored in
`kb_entries.embedding`, so the test is fast, offline and deterministic.

Tuned values (docs/rag_hyperparam_report_v3_joint.md):
    ANCHOR_QUANT_EPSILON = 0.02
    RAG_ANCHOR_TOP_K     = 8
    RAG_SCORE_THRESHOLD  = 0.65
    RAG_TOP_K            = 3

Usage (from repo root, PostgreSQL must be running and seeded):
    python scripts/test_tuned_hyperparams.py
"""
from __future__ import annotations

import os
import sys
import random
from pathlib import Path

# The BGE download can be broken by a stale CA bundle env var; clear defensively.
os.environ.pop("CURL_CA_BUNDLE", None)
os.environ.pop("REQUESTS_CA_BUNDLE", None)

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

EXPECTED = {
    "ANCHOR_QUANT_EPSILON": 0.02,
    "RAG_ANCHOR_TOP_K": 8,
    "RAG_SCORE_THRESHOLD": 0.65,
    "RAG_TOP_K": 3,
}

_passed = 0
_failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _failed
    mark = "PASS" if cond else "FAIL"
    if cond:
        _passed += 1
    else:
        _failed += 1
    print(f"  [{mark}] {name}{(' -> ' + detail) if detail else ''}")


def main() -> int:
    print("=" * 64)
    print("RAG 调优超参数应用验证")
    print("=" * 64)

    # ---- 1. settings 层：确认四个调优值已生效 -------------------------------
    from app.config import get_settings

    settings = get_settings()
    print("\n[1] 配置加载（app.config.get_settings）")
    for key, want in EXPECTED.items():
        got = getattr(settings, key)
        check(f"{key} = {got}", got == want, f"期望 {want}")

    # ---- 2. 准备：用库内已存向量作为查询，绕过 embedding 模型 ----------------
    import numpy as np
    from app.database import SessionLocal
    from app.models.knowledge import KBEntry
    from app.rag import retriever

    with SessionLocal() as db:
        entries = (
            db.query(KBEntry)
            .filter(KBEntry.embedding.isnot(None))
            .order_by(KBEntry.id)
            .limit(5)
            .all()
        )
        probe = [(e.id, e.question, list(e.embedding)) for e in entries]
        total = (
            db.query(KBEntry).filter(KBEntry.embedding.isnot(None)).count()
        )

    print(f"\n[2] 知识库样本：{total} 条带向量条目，取首条做自匹配查询")
    if not probe:
        print("  [FAIL] 知识库无带向量条目，无法测试检索（请先初始化/导入知识库）")
        return 1

    target_id, target_q, target_vec = probe[0]
    dim = len(target_vec)

    # 用一个可控的桩替换 embed_query：返回我们指定的向量，不加载模型
    _stub_vec = {"v": target_vec}
    retriever.embed_query = lambda text: _stub_vec["v"]

    # ---- 3. 命中路径：自匹配应在 τ=0.65 下命中且 score≈1.0 ------------------
    print("\n[3] 命中路径（query = 条目自身向量，模拟完美改写）")
    hits = retriever.search(target_q)  # 全部使用 settings 默认参数
    top = hits[0] if hits else None
    check("返回非空结果", bool(hits), f"{len(hits)} 条")
    if top:
        check(
            "Top-1 命中为目标条目",
            top["id"] == target_id,
            f"got id={top['id']}, score={top['score']}",
        )
        check("Top-1 score ≥ τ(0.65)", top["score"] >= 0.65, f"score={top['score']}")
    check(
        f"返回条数 ≤ RAG_TOP_K({settings.RAG_TOP_K})",
        len(hits) <= settings.RAG_TOP_K,
        f"{len(hits)} 条",
    )
    check(
        "所有返回 score 均 ≥ τ(0.65)",
        all(h["score"] >= 0.65 for h in hits),
        f"min={min((h['score'] for h in hits), default=None)}",
    )

    # ---- 4. 拒识路径：随机正交向量在 τ=0.65 下应被过滤 ----------------------
    print("\n[4] 拒识路径（query = 随机单位向量，应触发工单而非误命中）")
    rng = random.Random(42)
    rand = np.array([rng.gauss(0, 1) for _ in range(dim)], dtype=np.float64)
    rand = rand / (np.linalg.norm(rand) + 1e-12)
    _stub_vec["v"] = rand.tolist()
    neg = retriever.search("____noise____")
    check(
        "随机向量在 τ=0.65 下无误命中",
        len(neg) == 0,
        f"{len(neg)} 条 (top={neg[0]['score'] if neg else 'n/a'})",
    )

    # ---- 5. 阈值生效对比：同一查询，τ=0.40 vs τ=0.65 ----------------------
    print("\n[5] 阈值生效对比（同一自匹配查询，低阈值 vs 调优阈值）")
    _stub_vec["v"] = target_vec
    lo = retriever.search(target_q, threshold=0.40)
    hi = retriever.search(target_q, threshold=0.65)
    print(f"      τ=0.40 -> {len(lo)} 条；τ=0.65 -> {len(hi)} 条")
    check(
        "高阈值结果数 ≤ 低阈值结果数（更严格）",
        len(hi) <= len(lo),
        f"hi={len(hi)} <= lo={len(lo)}",
    )

    # ---- 汇总 ---------------------------------------------------------------
    print("\n" + "=" * 64)
    print(f"结果：PASS {_passed} / FAIL {_failed}")
    print("生效超参数：ε=%(ANCHOR_QUANT_EPSILON)s · L1-K=%(RAG_ANCHOR_TOP_K)s · "
          "τ=%(RAG_SCORE_THRESHOLD)s · Top-K=%(RAG_TOP_K)s" % {
              k: getattr(settings, k) for k in EXPECTED
          })
    print("=" * 64)
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
