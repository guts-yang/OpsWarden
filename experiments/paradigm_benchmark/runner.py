"""Main benchmark runner: execute 5 paradigms on the eval dataset."""
from __future__ import annotations

import json
import logging
import statistics
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .metrics import (
    PerQueryResult,
    aggregate,
    aggregate_topk_curve,
    hit_at_k,
    ndcg_at_k,
    reciprocal_rank,
)
from .paradigms import (
    FlatParadigm,
    GridTraceParadigm,
    HNSWParadigm,
    IVFParadigm,
    PageIndexParadigm,
    Paradigm,
)

logger = logging.getLogger("paradigm_benchmark")


def _make_paradigms(epsilon: float, anchor_k: int, threshold: float, n_probe: int) -> list[Paradigm]:
    return [
        FlatParadigm(),
        IVFParadigm(n_probe=n_probe),
        HNSWParadigm(M=16, ef_construction=64, ef_search=50),
        PageIndexParadigm(k_categories=1),
        GridTraceParadigm(epsilon=epsilon, anchor_k=anchor_k, threshold=threshold),
    ]


def _embed_query_text(embedder, text: str) -> list[float]:
    """Use the project embedder to get a 512-d vector."""
    from app.rag.embedder import embed_query  # local import

    return list(embed_query(text))


def _get_query_embedding(query: dict) -> list[float]:
    """Use query['embedding'] if present (synthetic / smoke), else embed the text."""
    if isinstance(query, dict) and query.get("embedding"):
        return list(query["embedding"])
    return _embed_query_text(None, query.get("query", ""))


def _embed_doc_joint(embedder, question: str, solution: str) -> list[float]:
    """Mirror production joint embedding: (q+s)/2 then L2-normalize."""
    from app.rag.eval_engine import compute_joint_embedding
    from app.rag.embedder import embed_document

    qv = np.asarray(embed_document(question), dtype=np.float64)
    sv = np.asarray(embed_document(solution), dtype=np.float64)
    joint = compute_joint_embedding(qv, sv)
    return joint.tolist()


def build_entries(kb_rows: list[dict]) -> list[dict]:
    """Build entries with embeddings.

    If a row already has an 'embedding' field, use it as-is (smoke / synthetic
    mode). Otherwise, compute the joint embedding via the production BGE
    embedder and cache to disk for reuse.
    """
    # Fast path: all rows already have embeddings (smoke / synthetic)
    if all(isinstance(r, dict) and r.get("embedding") for r in kb_rows):
        logger.info("All %d KB rows already have embeddings; skipping embedder", len(kb_rows))
        return kb_rows
    cache = Path(__file__).resolve().parent / ".kb_embeddings_cache.npz"
    expected = len(kb_rows)
    if cache.exists():
        try:
            data = np.load(cache, allow_pickle=True)
            if int(data.get("n", 0)) == expected and "embeddings" in data.files:
                logger.info("Loaded KB embedding cache (%d entries)", expected)
                embs = data["embeddings"]
                return [
                    {**row, "embedding": embs[i].tolist()}
                    for i, row in enumerate(kb_rows)
                ]
        except Exception as ex:  # pragma: no cover
            logger.warning("Failed to load KB embedding cache: %s; rebuilding", ex)
    logger.info("Computing KB joint embeddings for %d entries (one-time)...", expected)
    rows: list[dict] = []
    embs: list[np.ndarray] = []
    for row in kb_rows:
        v = _embed_doc_joint(None, row["question"], row["solution"])
        rows.append({**row, "embedding": v})
        embs.append(np.asarray(v, dtype=np.float32))
    np.savez(cache, embeddings=np.stack(embs), n=expected)
    return rows


def _run_one_query(
    paradigm: Paradigm,
    query_text: str,
    query_embedding: list[float],
    ground_truth: int,
    top_k: int,
    repeats: int,
) -> tuple[list[int], float]:
    """Run repeats of search, return (ranked page indices, median latency ms)."""
    latencies: list[float] = []
    best_ranked: list[int] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        hits = paradigm.search(query_text, query_embedding, top_k)
        latencies.append((time.perf_counter() - t0) * 1000.0)
        best_ranked = [h.page_index for h in hits]
    median_ms = float(statistics.median(latencies))
    return best_ranked, median_ms


def run_benchmark(
    kb_rows: list[dict],
    queries: list[dict],
    *,
    top_k: int = 3,
    repeats: int = 5,
    epsilon: float = 0.02,
    anchor_k: int = 8,
    threshold: float = 0.65,
    n_probe: int = 8,
) -> dict:
    """Run all 5 paradigms over all queries. Returns structured results dict."""
    entries = build_entries(kb_rows)
    paradigms = _make_paradigms(epsilon, anchor_k, threshold, n_probe)
    out: dict = {
        "config": {
            "top_k": top_k,
            "repeats": repeats,
            "epsilon": epsilon,
            "anchor_k": anchor_k,
            "threshold": threshold,
            "n_probe": n_probe,
            "n_queries": len(queries),
            "n_kb": len(kb_rows),
        },
        "index_stats": {},
        "per_query": {p.name: [] for p in paradigms},
        "aggregate": {},
    }
    # Build phase
    for p in paradigms:
        logger.info("Building %s ...", p.name)
        try:
            stats = p.build(entries)
            out["index_stats"][p.name] = {
                "build_time_sec": stats.build_time_sec,
                "index_size_bytes": stats.index_size_bytes,
                "extra": stats.extra,
            }
            logger.info("  %s: build=%.3fs, size=%d B", p.name, stats.build_time_sec, stats.index_size_bytes)
        except Exception as ex:
            logger.error("  %s BUILD FAILED: %s", p.name, ex)
            out["index_stats"][p.name] = {"error": str(ex)}
    # Query phase
    for qi, q in enumerate(queries):
        q_text = q["query"]
        gt = int(q["page_index"])
        q_emb = _get_query_embedding(q)
        for p in paradigms:
            if "error" in out["index_stats"][p.name]:
                continue
            ranked, lat_ms = _run_one_query(p, q_text, q_emb, gt, top_k, repeats)
            pqr = PerQueryResult(
                query_id=qi,
                ground_truth=gt,
                hit_at_1=hit_at_k(ranked, gt, 1),
                hit_at_3=hit_at_k(ranked, gt, 3),
                hit_at_5=hit_at_k(ranked, gt, 5),
                hit_at_10=hit_at_k(ranked, gt, 10),
                reciprocal_rank=reciprocal_rank(ranked, gt),
                latency_ms=lat_ms,
                ndcg_at_10=ndcg_at_k(ranked, gt, 10),
            )
            out["per_query"][p.name].append(pqr)
    # Aggregate
    for p in paradigms:
        out["aggregate"][p.name] = aggregate(out["per_query"][p.name])
    return out


def run_recall_latency_curve(
    kb_rows: list[dict],
    queries: list[dict],
    *,
    top_ks: list[int] | None = None,
    repeats: int = 3,
    epsilon: float = 0.02,
    anchor_k: int = 8,
    threshold: float = 0.65,
    n_probe: int = 8,
) -> dict:
    """Run all paradigms with varying top_k to produce Recall-Latency curve."""
    if top_ks is None:
        top_ks = [1, 3, 5, 10, 20]
    entries = build_entries(kb_rows)
    paradigms = _make_paradigms(epsilon, anchor_k, threshold, n_probe)
    # Build once
    for p in paradigms:
        try:
            p.build(entries)
        except Exception as ex:
            logger.error("%s build failed: %s", p.name, ex)
    out: dict = {p.name: {k: [] for k in top_ks} for p in paradigms}
    for k in top_ks:
        for qi, q in enumerate(queries):
            q_text = q["query"]
            gt = int(q["page_index"])
            q_emb = _get_query_embedding(q)
            for p in paradigms:
                ranked, lat_ms = _run_one_query(p, q_text, q_emb, gt, k, repeats)
                out[p.name][k].append(
                    PerQueryResult(
                        query_id=qi,
                        ground_truth=gt,
                        hit_at_1=hit_at_k(ranked, gt, 1),
                        hit_at_3=hit_at_k(ranked, gt, 3),
                        hit_at_5=hit_at_k(ranked, gt, 5),
                        hit_at_10=hit_at_k(ranked, gt, 10),
                        reciprocal_rank=reciprocal_rank(ranked, gt),
                        latency_ms=lat_ms,
                        ndcg_at_10=ndcg_at_k(ranked, gt, 10),
                    )
                )
    # Aggregate per top_k
    return {p.name: aggregate_topk_curve(out[p.name]) for p in paradigms}


def run_scaling(
    kb_rows: list[dict],
    queries: list[dict],
    *,
    sizes: list[int] | None = None,
    top_k: int = 3,
    repeats: int = 3,
    epsilon: float = 0.02,
    anchor_k: int = 8,
    threshold: float = 0.65,
    n_probe: int = 8,
) -> dict:
    """Re-sample KB to various sizes and run all paradigms.

    For N > len(kb_rows), we replicate entries with offset page_index.
    """
    if sizes is None:
        sizes = [100, 500, 1000, 5000, 10000]
    out: dict = {}
    for n in sizes:
        logger.info("=== Scale N=%d ===", n)
        sub_kb = _resample_kb(kb_rows, n)
        results = run_benchmark(
            sub_kb,
            queries,
            top_k=top_k,
            repeats=repeats,
            epsilon=epsilon,
            anchor_k=anchor_k,
            threshold=threshold,
            n_probe=n_probe,
        )
        out[n] = results["aggregate"]
    return out


def _resample_kb(kb_rows: list[dict], target_n: int) -> list[dict]:
    """Resample KB to target size by truncating or replicating with offset page_index."""
    if target_n <= len(kb_rows):
        return kb_rows[:target_n]
    out: list[dict] = list(kb_rows)
    base = len(kb_rows)
    i = 0
    while len(out) < target_n:
        src = kb_rows[i % base]
        offset = (i // base) * base
        out.append(
            {
                **src,
                "page_index": int(src["page_index"]) + offset,
            }
        )
        i += 1
    return out[:target_n]


def save_results(results: dict, path: Path) -> None:
    """Serialize results dict to JSON, handling numpy types."""
    def _conv(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, PerQueryResult):
            return asdict(o)
        raise TypeError(f"Not serializable: {type(o)}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, default=_conv, ensure_ascii=False, indent=2), encoding="utf-8")
