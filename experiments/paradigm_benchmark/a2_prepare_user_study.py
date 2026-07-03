"""A2 trail 用户感知评分 — 准备 30 条 query × 5 范式 trail 输出。

输出：
  - docs/PARADIGM_BENCHMARK_V3_A2_USER_STUDY.json
    （包含 30 条 query，每条 5 范式的 trail / 解释性字段）
  - docs/PARADIGM_BENCHMARK_V3_A2_USER_STUDY.md
    （供受试者阅读的 Markdown 表，每条 query 列出 5 范式输出）
  - docs/PARADIGM_BENCHMARK_V3_A2_SCORING_TEMPLATE.md
    （MOS 评分表 + 评分说明）

V3 设计的评分维度：
  1. causality（能否理解召回原因）0-5
  2. trust（能否判断结果可信度）0-5
  3. debuggability（能否定位失败原因）0-5
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ROOT / "experiments"
BENCH = EXPERIMENTS / "paradigm_benchmark"
BACKEND = ROOT / "backend"
SCRIPTS = ROOT / "scripts"
DOCS = ROOT / "docs"

if str(EXPERIMENTS) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS))
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from paradigm_benchmark.paradigms import (  # noqa: E402
    GridTraceEnhancedParadigm,
    GridTraceParadigm,
    HNSWParadigm,
    IVFParadigm,
    PageIndexParadigm,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("a2_prep")


def load_kb() -> list[dict]:
    return json.loads((SCRIPTS / "eval_datasets" / "faq_eval_kb_v3.json").read_text(encoding="utf-8"))


def load_queries() -> list[dict]:
    return json.loads((SCRIPTS / "eval_datasets" / "faq_eval_v3.json").read_text(encoding="utf-8"))


def select_diverse_queries(queries: list[dict], n: int = 30) -> list[dict]:
    """从 4 类 query 中按比例选 30 条（让评分样本覆盖多场景）。"""
    by_type: dict[str, list[dict]] = {}
    for q in queries:
        # v3 query 没有 type 字段；用 page_index 是否为 None 区分 negative
        t = "negative" if q.get("page_index") is None else "positive"
        by_type.setdefault(t, []).append(q)
    # 60% positive + 40% negative（让受试者既看到正确召回也看到负样本）
    n_pos = int(n * 0.6)
    n_neg = n - n_pos
    pos = by_type.get("positive", [])[:n_pos]
    neg = by_type.get("negative", [])[:n_neg]
    return pos + neg


def encode_zh(texts: list[str]):
    from sentence_transformers import SentenceTransformer
    import os
    os.environ['HF_HOME'] = 'd:/hf_cache'
    m = SentenceTransformer('BAAI/bge-small-zh-v1.5', device='cpu', cache_folder='d:/hf_cache')
    return m.encode(texts, batch_size=32, normalize_embeddings=True, convert_to_numpy=True).tolist()


def build_paradigm(name: str):
    if name == "GridTrace+":
        return GridTraceEnhancedParadigm(epsilon=0.02, epsilon_coarse=0.04, anchor_k=8, threshold=0.5)
    if name == "GridTrace":
        return GridTraceParadigm(epsilon=0.02, anchor_k=8, threshold=0.5)
    if name == "HNSW":
        return HNSWParadigm(M=16, ef_construction=200, ef_search=200)
    if name == "IVF":
        return IVFParadigm(n_probe=8)
    if name == "PageIndex":
        return PageIndexParadigm(k_categories=3)
    raise ValueError(name)


def format_paradigm_output(pname: str, hits: list) -> dict:
    """把 5 范式的输出格式化成「给用户看的版本」，保留可解释性字段。"""
    out = {
        "paradigm": pname,
        "top1": {
            "page_index": hits[0].page_index if hits else None,
            "score": round(hits[0].score, 3) if hits else None,
            "question": (hits[0].payload.get("question") or "")[:120] if hits else None,
            "category": hits[0].payload.get("category") if hits else None,
        },
        "explanation": "",  # 给用户看的解释
        "raw_trail": hits[0].payload.get("retrieval_trail", {}) if hits else {},
    }

    # 根据范式生成可读 explanation
    if pname == "GridTrace+":
        trail = out["raw_trail"]
        anchors = trail.get("l1_anchors", [])
        bucket_info = []
        for a in anchors[:3]:
            bucket_info.append(f"桶 #{a.get('anchor_idx')} (score={a.get('score', 0):.2f}, type={a.get('type', '?')})")
        rerank = trail.get("rerank_triggered", False)
        out["explanation"] = (
            f"🔍 **GridTrace+ L1 锚点命中**（{len(anchors)} 个）：\n"
            + "\n".join(f"  - {b}" for b in bucket_info)
            + f"\n📊 L1 候选数：{trail.get('l1_total_candidates', 0)} | 平均桶大小：{trail.get('l1_avg_bucket_size', 0):.1f}"
            + f"\n⚙️ 扩展环触发：{trail.get('l1_expansion_triggered', False)}（新增 {trail.get('l1_expansion_added', 0)} 桶）"
            + f"\n🎯 L3 Rerank 触发：{rerank}（候选 {trail.get('rerank_candidates', 0)}）"
        )
    elif pname == "GridTrace":
        out["explanation"] = (
            "🔍 **GridTrace（无增强）** 单层量化匹配\n"
            f"📊 返回 top-1 score: {out['top1']['score']}\n"
            "（无 trail 字段，无扩展环 / rerank）"
        )
    elif pname == "HNSW":
        out["explanation"] = (
            f"🚀 **HNSW KNN 图检索** (M=16, ef_search=200)\n"
            f"📊 返回 top-1 score: {out['top1']['score']}\n"
            "❌ 无任何 trail 字段——无法追溯「为什么这条被召回」"
        )
    elif pname == "IVF":
        out["explanation"] = (
            f"🗂️ **IVF 倒排聚类** (n_probe=8)\n"
            f"📊 返回 top-1 score: {out['top1']['score']}\n"
            "❌ 无 trail——只知 score，不知经过哪几个聚类"
        )
    elif pname == "PageIndex":
        out["explanation"] = (
            f"📑 **PageIndex 类别树 + BM25**\n"
            f"📊 命中类别：{out['top1']['category']}\n"
            "（BM25 关键词匹配路径，可解释性中等）"
        )

    return out


def main():
    logger.info("=" * 60)
    logger.info("A2 用户研究数据准备")
    logger.info("=" * 60)
    kb_rows = load_kb()
    queries = load_queries()
    # 选 30 条 query
    study_queries = select_diverse_queries(queries, 30)
    logger.info("  选 %d 条 query: %d 正样本 + %d 负样本",
                len(study_queries),
                sum(1 for q in study_queries if q.get("page_index") is not None),
                sum(1 for q in study_queries if q.get("page_index") is None))
    # 编码 query + KB
    kb_texts = [r["question"] + "\n" + r["solution"] for r in kb_rows]
    logger.info("  编码 KB...")
    kb_vecs = encode_zh(kb_texts)
    logger.info("  编码 query...")
    q_texts = [q["query"] for q in study_queries]
    q_vecs = encode_zh(q_texts)
    # KB entries（含 embedding）
    entries = [
        {
            "page_index": r["page_index"],
            "question": r["question"],
            "solution": r["solution"],
            "category": r.get("category", ""),
            "embedding": v,
        }
        for r, v in zip(kb_rows, kb_vecs)
    ]

    # 5 个范式
    paradigms = ["GridTrace+", "GridTrace", "HNSW", "IVF", "PageIndex"]
    paradigm_objs = {n: build_paradigm(n) for n in paradigms}
    for n, p in paradigm_objs.items():
        logger.info("  Build %s ...", n)
        p.build(entries)

    # 对每条 query 跑 5 范式
    out_data = []
    for qi, (q, qv) in enumerate(zip(study_queries, q_vecs)):
        logger.info("  Query %d/%d: %s", qi + 1, len(study_queries), q["query"][:40])
        per_p = {}
        for pname, p in paradigm_objs.items():
            try:
                hits = p.search(q["query"], qv, top_k=3)
                per_p[pname] = format_paradigm_output(pname, hits)
            except Exception as ex:
                per_p[pname] = {"paradigm": pname, "error": str(ex)}
        out_data.append({
            "query_id": qi,
            "query_text": q["query"],
            "ground_truth_page_index": q.get("page_index"),
            "is_negative": q.get("page_index") is None,
            "paradigm_outputs": per_p,
        })

    # 保存 JSON
    out_json = {
        "version": "v3_a2",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "n_queries": len(out_data),
        "n_paradigms": len(paradigms),
        "queries": out_data,
    }
    json_path = DOCS / "PARADIGM_BENCHMARK_V3_A2_USER_STUDY.json"
    json_path.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("  WROTE %s (%d KB)", json_path, json_path.stat().st_size // 1024)

    # 生成受试者用的 Markdown
    md_lines = [
        "# A2 trail 用户感知评分 — 受试者用表",
        "",
        f"_生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "## 受试者说明",
        "",
        "**任务**：对 30 条 query 评估 5 个范式的输出，回答 3 个维度（每条 0-5 分）：",
        "1. **causality（召回原因可理解性）**：看解释能否理解「为什么这条被召回」",
        "2. **trust（结果可信度）**：看解释能否判断「这条结果是否可信」",
        "3. **debuggability（失败定位）**：看解释能否帮助定位「为何召回失败 / 召回错误」",
        "",
        "**评分标准**：",
        "- 0 = 完全无法判断 / 无信息",
        "- 1 = 几乎无帮助",
        "- 2 = 部分信息但不够",
        "- 3 = 一般",
        "- 4 = 较好",
        "- 5 = 完全能理解 / 充分可信 / 容易定位",
        "",
        "---",
        "",
    ]
    for qi, qd in enumerate(out_data):
        qt = qd['query_text'][:80] + ('...' if len(qd['query_text']) > 80 else '')
        gt_pid = qd.get('ground_truth_page_index')
        if qd['is_negative']:
            type_label = '负样本（不应召回）'
        else:
            type_label = f'正样本（ground_truth = page #{gt_pid}）'
        md_lines.extend([
            f"## Query {qi + 1}: {qt}",
            "",
            f"**类型**：{type_label}",
            "",
        ])
        for pname in paradigms:
            po = qd["paradigm_outputs"].get(pname, {})
            md_lines.extend([
                f"### {pname}",
                "",
                po.get("explanation", "(无输出)"),
                "",
                f"**Top-1 召回**：page #{po.get('top1', {}).get('page_index', '?')}, score={po.get('top1', {}).get('score', '?')}",
                "",
                "**评分**（请打分 0-5）：",
                "",
                "| 维度 | 评分 (0-5) |",
                "|---|---|",
                "| causality 召回原因可理解性 | ___ |",
                "| trust 结果可信度 | ___ |",
                "| debuggability 失败定位 | ___ |",
                "",
            ])
        md_lines.extend(["---", ""])

    md_path = DOCS / "PARADIGM_BENCHMARK_V3_A2_USER_STUDY.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    logger.info("  WROTE %s (%d KB)", md_path, md_path.stat().st_size // 1024)

    # 评分模板（汇总表）
    scoring = f"""# A2 评分模板

**受试者**：__________  **日期**：__________  **从业年限**：__________

## 评分汇总表（30 query × 5 范式 × 3 维度 = 450 个评分）

| Query # | 范式 | causality (0-5) | trust (0-5) | debuggability (0-5) | 备注 |
|---|---|---|---|---|---|
"""
    for qi in range(len(out_data)):
        for pname in paradigms:
            scoring += f"| Q{qi + 1} | {pname} | ___ | ___ | ___ | |\n"

    scoring += """

## MOS 计算公式

每个范式的 MOS（Mean Opinion Score）：
```
MOS = mean(causality, trust, debuggability)
```

最终对比：
- GridTrace+ MOS = ____
- GridTrace MOS = ____
- HNSW MOS = ____
- IVF MOS = ____
- PageIndex MOS = ____

## 显著性检验（推荐）

- 配对 Wilcoxon signed-rank test：GridTrace+ vs HNSW（per-query MOS 配对）
- Cohen's d 效应量
- 95% 置信区间

## 提交

将填写好的评分表提交到 OpsWarden 团队，路径：`docs/PARADIGM_BENCHMARK_V3_A2_RESULTS_HUMAN_<name>.md`
"""
    scoring_path = DOCS / "PARADIGM_BENCHMARK_V3_A2_SCORING_TEMPLATE.md"
    scoring_path.write_text(scoring, encoding="utf-8")
    logger.info("  WROTE %s", scoring_path)
    print("\nA2 user study data prep DONE.")


if __name__ == "__main__":
    main()
