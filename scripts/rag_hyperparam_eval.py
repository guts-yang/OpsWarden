#!/usr/bin/env python3
"""RAG hyperparameter grid search (in-memory) with embedding cache.

Usage (from repo root):
    python scripts/build_eval_dataset_v2.py
    python scripts/rag_hyperparam_eval.py --dataset v2 --all
    python scripts/rag_hyperparam_eval.py --dataset v3 --joint3 --all
    python scripts/rag_hyperparam_eval.py --dataset v1 --all
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np

os.environ.pop("CURL_CA_BUNDLE", None)
os.environ.pop("REQUESTS_CA_BUNDLE", None)

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
SCRIPTS = ROOT / "scripts"
CACHE_DIR = SCRIPTS / ".eval_cache"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.rag.embedder import embed_document, embed_query  # noqa: E402
from app.rag.eval_engine import (  # noqa: E402
    EvalEntry,
    build_anchors,
    compute_joint_embedding,
    l1_anchor_hit,
    rank_all_candidates,
    search_inmemory,
)
from app.rag.faq_loader import FAQ_PATH, _parse_faq  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rag_hyperparam_eval")

# v1 defaults
DEFAULT_EPS = [0.01, 0.02, 0.03, 0.05, 0.08, 0.10]
DEFAULT_ANCHOR_K_V1 = [4, 8, 12, 16, 24]
DEFAULT_THRESHOLD_V1 = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
DEFAULT_TOP_K = [1, 3, 5]

# v2 expanded grid
DEFAULT_ANCHOR_K_V2 = [1, 2, 3, 4, 8, 12, 16, 24]
DEFAULT_THRESHOLD_V2 = [round(x * 0.05, 2) for x in range(7, 18)]  # 0.35 .. 0.85

# v3 joint3: fixed tau, tune epsilon + L1-K + Top-K
FIXED_THRESHOLD_V3 = 0.65
N_CANONICAL_PAGES = 100
DEFAULT_EPS_V3 = [0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.12, 0.15]
DEFAULT_ANCHOR_K_V3 = [1, 2, 3, 4, 6, 8, 12, 16, 24]

DEFAULT_FPR_MAX = 0.05

BASELINE = {"epsilon": 0.02, "anchor_k": 8, "threshold": 0.40, "top_k": 3}


def paths_for(dataset_version: str) -> dict[str, Path]:
    if dataset_version == "v3":
        return {
            "dataset": SCRIPTS / "eval_datasets" / "faq_eval_v3.json",
            "kb": SCRIPTS / "eval_datasets" / "faq_eval_kb_v3.json",
            "embeddings": CACHE_DIR / "faq_eval_v3_embeddings.npz",
            "grid": CACHE_DIR / "grid_results_v3_joint.csv",
            "top5": CACHE_DIR / "top5_configs_v3_joint.json",
        }
    if dataset_version == "v2":
        return {
            "dataset": SCRIPTS / "eval_datasets" / "faq_eval_v2.json",
            "embeddings": CACHE_DIR / "faq_eval_v2_embeddings.npz",
            "grid": CACHE_DIR / "grid_results_v2.csv",
            "top5": CACHE_DIR / "top5_configs_v2.json",
        }
    return {
        "dataset": SCRIPTS / "eval_datasets" / "faq_exact.json",
        "embeddings": CACHE_DIR / "faq_embeddings.npz",
        "grid": CACHE_DIR / "grid_results.csv",
        "top5": CACHE_DIR / "top5_configs.json",
    }


def build_faq_exact_dataset() -> list[dict]:
    parsed = _parse_faq(FAQ_PATH.read_text(encoding="utf-8"))
    return [
        {
            "query": item["question"],
            "page_index": idx,
            "split": "exact",
            "paraphrase_id": None,
            "category": item["category"],
            "question": item["question"],
            "solution": item["solution"],
        }
        for idx, item in enumerate(parsed, start=1)
    ]


def load_dataset(dataset_version: str) -> list[dict]:
    p = paths_for(dataset_version)["dataset"]
    if dataset_version == "v3":
        if not p.exists():
            import subprocess
            subprocess.run([sys.executable, str(SCRIPTS / "build_eval_dataset_v3.py")], check=True)
        return json.loads(p.read_text(encoding="utf-8"))
    if dataset_version == "v2":
        if not p.exists():
            import subprocess
            subprocess.run([sys.executable, str(SCRIPTS / "build_eval_dataset_v2.py")], check=True)
        return json.loads(p.read_text(encoding="utf-8"))
    if not p.exists():
        data = build_faq_exact_dataset()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return json.loads(p.read_text(encoding="utf-8"))


def load_eval_kb_v3(kb_path: Path) -> list[dict]:
    if not kb_path.exists():
        import subprocess
        subprocess.run([sys.executable, str(SCRIPTS / "build_eval_dataset_v3.py")], check=True)
    return json.loads(kb_path.read_text(encoding="utf-8"))


def kb_entries_from_faq() -> list[dict]:
    parsed = _parse_faq(FAQ_PATH.read_text(encoding="utf-8"))
    return [
        {
            "page_index": idx,
            "category": item["category"],
            "question": item["question"],
            "solution": item["solution"],
        }
        for idx, item in enumerate(parsed, start=1)
    ]


def build_embedding_cache_v3(
    dataset: list[dict],
    kb_rows: list[dict],
    embeddings_path: Path,
) -> tuple[list[EvalEntry], list[np.ndarray]]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[EvalEntry] = []

    logger.info("Computing v3 KB joint embeddings for %d entries...", len(kb_rows))
    started = time.time()
    for item in kb_rows:
        q_text = item["question"].strip()
        s_text = item["solution"].strip()
        qv = np.asarray(embed_document(q_text), dtype=np.float64)
        sv = np.asarray(embed_document(s_text), dtype=np.float64)
        joint = compute_joint_embedding(qv, sv)
        entries.append(
            EvalEntry(
                page_index=int(item["page_index"]),
                question=q_text,
                solution=s_text,
                category=item["category"],
                embedding=joint,
            )
        )

    logger.info("Computing query embeddings for %d eval queries...", len(dataset))
    query_vectors = [np.asarray(embed_query(item["query"]), dtype=np.float64) for item in dataset]

    np.savez(
        embeddings_path,
        page_index=np.array([e.page_index for e in entries], dtype=np.int32),
        joint_embeddings=np.stack([e.embedding for e in entries]),
        query_embeddings=np.stack(query_vectors),
        questions=np.array([e.question for e in entries], dtype=object),
        solutions=np.array([e.solution for e in entries], dtype=object),
        categories=np.array([e.category for e in entries], dtype=object),
        n_eval_queries=len(dataset),
        n_kb_entries=len(kb_rows),
    )
    logger.info("Cached embeddings to %s (%.1fs)", embeddings_path, time.time() - started)
    return entries, query_vectors


def build_embedding_cache(
    dataset: list[dict],
    embeddings_path: Path,
    *,
    dataset_version: str = "v1",
    kb_path: Path | None = None,
) -> tuple[list[EvalEntry], list[np.ndarray]]:
    if dataset_version == "v3":
        kb_rows = load_eval_kb_v3(kb_path or paths_for("v3")["kb"])
        return build_embedding_cache_v3(dataset, kb_rows, embeddings_path)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    kb_rows = kb_entries_from_faq()
    entries: list[EvalEntry] = []

    logger.info("Computing KB joint embeddings for %d FAQ entries...", len(kb_rows))
    started = time.time()
    for item in kb_rows:
        q_text = item["question"].strip()
        s_text = item["solution"].strip()
        qv = np.asarray(embed_document(q_text), dtype=np.float64)
        sv = np.asarray(embed_document(s_text), dtype=np.float64)
        joint = compute_joint_embedding(qv, sv)
        entries.append(
            EvalEntry(
                page_index=int(item["page_index"]),
                question=q_text,
                solution=s_text,
                category=item["category"],
                embedding=joint,
            )
        )

    logger.info("Computing query embeddings for %d eval queries...", len(dataset))
    query_vectors = [np.asarray(embed_query(item["query"]), dtype=np.float64) for item in dataset]

    np.savez(
        embeddings_path,
        page_index=np.array([e.page_index for e in entries], dtype=np.int32),
        joint_embeddings=np.stack([e.embedding for e in entries]),
        query_embeddings=np.stack(query_vectors),
        questions=np.array([e.question for e in entries], dtype=object),
        solutions=np.array([e.solution for e in entries], dtype=object),
        categories=np.array([e.category for e in entries], dtype=object),
        n_eval_queries=len(dataset),
    )
    logger.info("Cached embeddings to %s (%.1fs)", embeddings_path, time.time() - started)
    return entries, query_vectors


def load_embedding_cache(
    dataset: list[dict],
    embeddings_path: Path,
    *,
    dataset_version: str = "v1",
    kb_path: Path | None = None,
) -> tuple[list[EvalEntry], list[np.ndarray]]:
    if dataset_version == "v3":
        kb_rows = load_eval_kb_v3(kb_path or paths_for("v3")["kb"])
        n_kb = len(kb_rows)
        if not embeddings_path.exists():
            return build_embedding_cache_v3(dataset, kb_rows, embeddings_path)
        data = np.load(embeddings_path, allow_pickle=True)
        n_eval = int(data.get("n_eval_queries", len(data["query_embeddings"])))
        n_kb_cached = int(data.get("n_kb_entries", len(data["page_index"])))
        if n_kb_cached != n_kb or n_eval != len(dataset):
            logger.warning("Cache mismatch; rebuilding...")
            return build_embedding_cache_v3(dataset, kb_rows, embeddings_path)
        entries = [
            EvalEntry(
                page_index=int(data["page_index"][i]),
                question=str(data["questions"][i]),
                solution=str(data["solutions"][i]),
                category=str(data["categories"][i]),
                embedding=np.asarray(data["joint_embeddings"][i], dtype=np.float64),
            )
            for i in range(len(data["page_index"]))
        ]
        query_vectors = [np.asarray(v, dtype=np.float64) for v in data["query_embeddings"]]
        logger.info("Loaded cache: %d KB entries, %d queries", len(entries), len(query_vectors))
        return entries, query_vectors

    if not embeddings_path.exists():
        return build_embedding_cache(dataset, embeddings_path, dataset_version=dataset_version)

    data = np.load(embeddings_path, allow_pickle=True)
    n_eval = int(data.get("n_eval_queries", len(data["query_embeddings"])))
    if len(data["page_index"]) != 100 or n_eval != len(dataset):
        logger.warning("Cache mismatch; rebuilding...")
        return build_embedding_cache(dataset, embeddings_path, dataset_version=dataset_version)

    entries = [
        EvalEntry(
            page_index=int(data["page_index"][i]),
            question=str(data["questions"][i]),
            solution=str(data["solutions"][i]),
            category=str(data["categories"][i]),
            embedding=np.asarray(data["joint_embeddings"][i], dtype=np.float64),
        )
        for i in range(len(data["page_index"]))
    ]
    query_vectors = [np.asarray(v, dtype=np.float64) for v in data["query_embeddings"]]
    logger.info("Loaded cache: %d KB entries, %d queries", len(entries), len(query_vectors))
    return entries, query_vectors


def evaluate_config_v1(
    entries: list[EvalEntry],
    query_vectors: list[np.ndarray],
    dataset: list[dict],
    epsilon: float,
    anchor_k: int,
    threshold: float,
    top_k: int,
) -> dict:
    eval_entries = [
        EvalEntry(
            page_index=e.page_index,
            question=e.question,
            solution=e.solution,
            category=e.category,
            embedding=e.embedding.copy(),
        )
        for e in entries
    ]
    anchors = build_anchors(eval_entries, epsilon)
    hit1_thresh = hit1_raw = l1_recall = recall_at_k = 0
    correct_scores: list[float] = []

    for qvec, item in zip(query_vectors, dataset):
        expected = int(item["page_index"])
        hits, _ = search_inmemory(
            qvec, eval_entries, anchors, anchor_k=anchor_k, threshold=threshold, top_k=top_k
        )
        ranked, l1_idx = rank_all_candidates(qvec, eval_entries, anchors, anchor_k=anchor_k)
        if ranked:
            top_page = eval_entries[ranked[0][0]].page_index
            if top_page == expected:
                hit1_raw += 1
                correct_scores.append(ranked[0][1])
            if hits and hits[0]["page_index"] == expected:
                hit1_thresh += 1
        hit_pages = {eval_entries[idx].page_index for idx, _ in ranked[:top_k]}
        if expected in hit_pages:
            recall_at_k += 1
        if l1_anchor_hit(eval_entries, anchors, expected, l1_idx):
            l1_recall += 1

    n = len(dataset)
    return {
        "epsilon": epsilon,
        "anchor_k": anchor_k,
        "threshold": threshold,
        "top_k": top_k,
        "n_queries": n,
        "n_anchors": len(anchors),
        "hit1_with_threshold": hit1_thresh / n,
        "hit1_no_threshold": hit1_raw / n,
        "l1_anchor_recall": l1_recall / n,
        "recall_at_k": recall_at_k / n,
        "median_correct_score": float(np.median(correct_scores)) if correct_scores else 0.0,
        "min_correct_score": float(np.min(correct_scores)) if correct_scores else 0.0,
    }


def evaluate_config_v2(
    entries: list[EvalEntry],
    query_vectors: list[np.ndarray],
    dataset: list[dict],
    epsilon: float,
    anchor_k: int,
    threshold: float,
    top_k: int,
) -> dict:
    eval_entries = [
        EvalEntry(
            page_index=e.page_index,
            question=e.question,
            solution=e.solution,
            category=e.category,
            embedding=e.embedding.copy(),
        )
        for e in entries
    ]
    anchors = build_anchors(eval_entries, epsilon)

    exact_hit = para_hit = exact_n = para_n = neg_n = neg_fp = 0
    l1_para_hit = para_n_l1 = 0
    mrr_sum = 0.0
    margins: list[float] = []
    neg_top_scores: list[float] = []

    for qvec, item in zip(query_vectors, dataset):
        split = item.get("split", "exact")
        ranked, l1_idx = rank_all_candidates(qvec, eval_entries, anchors, anchor_k=anchor_k)
        hits, _ = search_inmemory(
            qvec, eval_entries, anchors, anchor_k=anchor_k, threshold=threshold, top_k=top_k
        )

        if split in ("exact", "paraphrase"):
            expected = int(item["page_index"])
            if split == "exact":
                exact_n += 1
            else:
                para_n += 1
                if l1_anchor_hit(eval_entries, anchors, expected, l1_idx):
                    l1_para_hit += 1
                    para_n_l1 += 1
                else:
                    para_n_l1 += 1
                # MRR
                rr = 0.0
                for rank, (idx, _) in enumerate(ranked, start=1):
                    if eval_entries[idx].page_index == expected:
                        rr = 1.0 / rank
                        break
                mrr_sum += rr

            if ranked and eval_entries[ranked[0][0]].page_index == expected:
                if len(ranked) >= 2:
                    margins.append(ranked[0][1] - ranked[1][1])
                elif len(ranked) == 1:
                    margins.append(ranked[0][1])

            hit_ok = bool(hits and hits[0]["page_index"] == expected)
            if split == "exact" and hit_ok:
                exact_hit += 1
            elif split == "paraphrase" and hit_ok:
                para_hit += 1

        elif split == "negative":
            neg_n += 1
            top_score = ranked[0][1] if ranked else 0.0
            neg_top_scores.append(top_score)
            if top_score >= threshold:
                neg_fp += 1

    row = {
        "epsilon": epsilon,
        "anchor_k": anchor_k,
        "threshold": threshold,
        "top_k": top_k,
        "n_anchors": len(anchors),
        "n_exact": exact_n,
        "n_paraphrase": para_n,
        "n_negative": neg_n,
        "hit1_exact": exact_hit / exact_n if exact_n else 0.0,
        "hit1_para": para_hit / para_n if para_n else 0.0,
        "fpr": neg_fp / neg_n if neg_n else 0.0,
        "l1_recall_para": l1_para_hit / para_n_l1 if para_n_l1 else 0.0,
        "mrr_para": mrr_sum / para_n if para_n else 0.0,
        "score_margin_median": float(np.median(margins)) if margins else 0.0,
        "neg_top_score_median": float(np.median(neg_top_scores)) if neg_top_scores else 0.0,
        "neg_top_score_max": float(np.max(neg_top_scores)) if neg_top_scores else 0.0,
    }
    return row


def evaluate_config_v3(
    entries: list[EvalEntry],
    query_vectors: list[np.ndarray],
    dataset: list[dict],
    epsilon: float,
    anchor_k: int,
    threshold: float,
    top_k: int,
) -> dict:
    eval_entries = [
        EvalEntry(
            page_index=e.page_index,
            question=e.question,
            solution=e.solution,
            category=e.category,
            embedding=e.embedding.copy(),
        )
        for e in entries
    ]
    anchors = build_anchors(eval_entries, epsilon)
    n_anchors = len(anchors)
    anchor_compression = N_CANONICAL_PAGES / n_anchors if n_anchors else 0.0

    exact_hit = para_hit = hard_hit = exact_n = para_n = hard_n = neg_n = neg_fp = 0
    l1_para_hit = para_n_l1 = l1_hard_hit = hard_n_l1 = 0
    recall_at_k_para_hit = 0
    mrr_sum = 0.0
    margins: list[float] = []
    neg_top_scores: list[float] = []

    for qvec, item in zip(query_vectors, dataset):
        split = item.get("split", "exact")
        ranked, l1_idx = rank_all_candidates(qvec, eval_entries, anchors, anchor_k=anchor_k)
        hits, _ = search_inmemory(
            qvec, eval_entries, anchors, anchor_k=anchor_k, threshold=threshold, top_k=top_k
        )

        if split in ("exact", "paraphrase", "hard_confusion"):
            expected = int(item["page_index"])
            if split == "exact":
                exact_n += 1
            elif split == "paraphrase":
                para_n += 1
                if l1_anchor_hit(eval_entries, anchors, expected, l1_idx):
                    l1_para_hit += 1
                para_n_l1 += 1
                rr = 0.0
                for rank, (idx, _) in enumerate(ranked, start=1):
                    if eval_entries[idx].page_index == expected:
                        rr = 1.0 / rank
                        break
                mrr_sum += rr
                hit_pages = {h["page_index"] for h in hits}
                if expected in hit_pages:
                    recall_at_k_para_hit += 1
            else:
                hard_n += 1
                if l1_anchor_hit(eval_entries, anchors, expected, l1_idx):
                    l1_hard_hit += 1
                hard_n_l1 += 1

            if ranked and eval_entries[ranked[0][0]].page_index == expected:
                if len(ranked) >= 2:
                    margins.append(ranked[0][1] - ranked[1][1])
                elif len(ranked) == 1:
                    margins.append(ranked[0][1])

            hit_ok = bool(hits and hits[0]["page_index"] == expected)
            if split == "exact" and hit_ok:
                exact_hit += 1
            elif split == "paraphrase" and hit_ok:
                para_hit += 1
            elif split == "hard_confusion" and hit_ok:
                hard_hit += 1

        elif split == "negative":
            neg_n += 1
            top_score = ranked[0][1] if ranked else 0.0
            neg_top_scores.append(top_score)
            if top_score >= threshold:
                neg_fp += 1

    return {
        "epsilon": epsilon,
        "anchor_k": anchor_k,
        "threshold": threshold,
        "top_k": top_k,
        "n_anchors": n_anchors,
        "anchor_compression": anchor_compression,
        "n_kb_entries": len(eval_entries),
        "n_exact": exact_n,
        "n_paraphrase": para_n,
        "n_hard_confusion": hard_n,
        "n_negative": neg_n,
        "hit1_exact": exact_hit / exact_n if exact_n else 0.0,
        "hit1_para": para_hit / para_n if para_n else 0.0,
        "hit1_hard": hard_hit / hard_n if hard_n else 0.0,
        "fpr": neg_fp / neg_n if neg_n else 0.0,
        "l1_recall_para": l1_para_hit / para_n_l1 if para_n_l1 else 0.0,
        "l1_recall_hard": l1_hard_hit / hard_n_l1 if hard_n_l1 else 0.0,
        "recall_at_k_para": recall_at_k_para_hit / para_n if para_n else 0.0,
        "mrr_para": mrr_sum / para_n if para_n else 0.0,
        "score_margin_median": float(np.median(margins)) if margins else 0.0,
        "neg_top_score_median": float(np.median(neg_top_scores)) if neg_top_scores else 0.0,
        "neg_top_score_max": float(np.max(neg_top_scores)) if neg_top_scores else 0.0,
    }


def config_sort_key_v3_joint(row: dict, fpr_max: float) -> tuple:
    feasible = row["fpr"] <= fpr_max + 1e-9
    return (
        1 if feasible else 0,
        row["hit1_para"],
        row["l1_recall_hard"],
        row["recall_at_k_para"],
        row["anchor_compression"],
        -row["anchor_k"],
        -abs(row["top_k"] - 3),
        row["epsilon"],
    )


def config_sort_key_v1(row: dict) -> tuple:
    return (
        row["hit1_with_threshold"],
        row["threshold"],
        -row["anchor_k"],
        row["epsilon"],
        -abs(row["top_k"] - 3),
    )


def config_sort_key_v2(row: dict, fpr_max: float) -> tuple:
    feasible = row["fpr"] <= fpr_max + 1e-9
    return (
        1 if feasible else 0,
        row["hit1_para"],
        row["threshold"],
        -row["fpr"],
        -row["anchor_k"],
        row["epsilon"],
        -abs(row["top_k"] - 3),
    )


def run_grid(
    entries: list[EvalEntry],
    query_vectors: list[np.ndarray],
    dataset: list[dict],
    epsilons: list[float],
    anchor_ks: list[int],
    thresholds: list[float],
    top_ks: list[int],
    dataset_version: str,
    grid_csv: Path,
    fpr_max: float,
) -> list[dict]:
    eval_fn = evaluate_config_v2 if dataset_version == "v2" else evaluate_config_v1
    sort_fn = (
        (lambda r: config_sort_key_v2(r, fpr_max))
        if dataset_version == "v2"
        else config_sort_key_v1
    )

    combos = list(product(epsilons, anchor_ks, thresholds, top_ks))
    results: list[dict] = []
    best: dict | None = None
    started = time.time()

    logger.info("Running grid search (%s): %d configurations", dataset_version, len(combos))
    for i, (eps, ak, th, tk) in enumerate(combos, start=1):
        row = eval_fn(entries, query_vectors, dataset, eps, ak, th, tk)
        results.append(row)
        if best is None or sort_fn(row) > sort_fn(best):
            best = row
        if i % 100 == 0 or i == len(combos):
            if dataset_version == "v2":
                logger.info(
                    "[%d/%d] best: eps=%.2f ak=%d th=%.2f hit_para=%.3f fpr=%.3f",
                    i, len(combos), best["epsilon"], best["anchor_k"], best["threshold"],
                    best["hit1_para"], best["fpr"],
                )
            else:
                logger.info(
                    "[%d/%d] best: hit@1=%.3f th=%.2f",
                    i, len(combos), best["hit1_with_threshold"], best["threshold"],
                )

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with grid_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    logger.info("Grid saved to %s (%.1fs)", grid_csv, time.time() - started)
    return results


def run_grid_joint3(
    entries: list[EvalEntry],
    query_vectors: list[np.ndarray],
    dataset: list[dict],
    epsilons: list[float],
    anchor_ks: list[int],
    top_ks: list[int],
    threshold: float,
    grid_csv: Path,
    fpr_max: float,
) -> list[dict]:
    combos = list(product(epsilons, anchor_ks, top_ks))
    results: list[dict] = []
    best: dict | None = None
    sort_fn = lambda r: config_sort_key_v3_joint(r, fpr_max)
    started = time.time()

    logger.info("Running v3 joint3 grid (tau=%.2f): %d configurations", threshold, len(combos))
    for i, (eps, ak, tk) in enumerate(combos, start=1):
        row = evaluate_config_v3(entries, query_vectors, dataset, eps, ak, threshold, tk)
        results.append(row)
        if best is None or sort_fn(row) > sort_fn(best):
            best = row
        if i % 50 == 0 or i == len(combos):
            logger.info(
                "[%d/%d] best: eps=%.2f ak=%d tk=%d hit_para=%.3f l1_hard=%.3f "
                "recall@k=%.3f anchors=%d fpr=%.3f",
                i, len(combos), best["epsilon"], best["anchor_k"], best["top_k"],
                best["hit1_para"], best["l1_recall_hard"], best["recall_at_k_para"],
                best["n_anchors"], best["fpr"],
            )

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with grid_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    logger.info("Grid saved to %s (%.1fs)", grid_csv, time.time() - started)
    return results


def select_top_configs(
    results: list[dict],
    top5_path: Path,
    dataset_version: str,
    n: int,
    fpr_max: float,
) -> list[dict]:
    if dataset_version == "v3":
        ranked = sorted(results, key=lambda r: config_sort_key_v3_joint(r, fpr_max), reverse=True)
    elif dataset_version == "v2":
        ranked = sorted(results, key=lambda r: config_sort_key_v2(r, fpr_max), reverse=True)
    else:
        ranked = sorted(results, key=config_sort_key_v1, reverse=True)

    seen: set[tuple] = set()
    top: list[dict] = []
    for row in ranked:
        key = (row["epsilon"], row["anchor_k"], row["threshold"], row["top_k"])
        if key in seen:
            continue
        seen.add(key)
        item = {
            "rank": len(top) + 1,
            "epsilon": row["epsilon"],
            "anchor_k": int(row["anchor_k"]),
            "threshold": row["threshold"],
            "top_k": int(row["top_k"]),
            "n_anchors": int(row["n_anchors"]),
        }
        if dataset_version == "v3":
            item.update(
                {
                    "hit1_exact": row["hit1_exact"],
                    "hit1_para": row["hit1_para"],
                    "hit1_hard": row["hit1_hard"],
                    "fpr": row["fpr"],
                    "l1_recall_para": row["l1_recall_para"],
                    "l1_recall_hard": row["l1_recall_hard"],
                    "recall_at_k_para": row["recall_at_k_para"],
                    "anchor_compression": row["anchor_compression"],
                    "mrr_para": row["mrr_para"],
                    "score_margin_median": row["score_margin_median"],
                }
            )
        elif dataset_version == "v2":
            item.update(
                {
                    "hit1_exact": row["hit1_exact"],
                    "hit1_para": row["hit1_para"],
                    "fpr": row["fpr"],
                    "l1_recall_para": row["l1_recall_para"],
                    "mrr_para": row["mrr_para"],
                    "score_margin_median": row["score_margin_median"],
                }
            )
        else:
            item.update(
                {
                    "hit1_with_threshold": row["hit1_with_threshold"],
                    "hit1_no_threshold": row["hit1_no_threshold"],
                    "l1_anchor_recall": row["l1_anchor_recall"],
                    "median_correct_score": row["median_correct_score"],
                }
            )
        top.append(item)
        if len(top) >= n:
            break

    top5_path.write_text(json.dumps(top, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Top-%d saved to %s", n, top5_path)
    return top


def parse_float_list(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",") if x.strip()]


def parse_int_list(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG hyperparameter grid search")
    parser.add_argument("--dataset", choices=["v1", "v2", "v3"], default="v2")
    parser.add_argument("--joint3", action="store_true", help="v3: fixed tau, tune eps/L1-K/Top-K")
    parser.add_argument("--build-cache", action="store_true")
    parser.add_argument("--grid", action="store_true")
    parser.add_argument("--select-top", type=int, default=5)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--fpr-max", type=float, default=DEFAULT_FPR_MAX)
    parser.add_argument("--fixed-threshold", type=float, default=FIXED_THRESHOLD_V3)
    parser.add_argument("--epsilons", type=str, default="")
    parser.add_argument("--anchor-k", type=str, default="")
    parser.add_argument("--thresholds", type=str, default="")
    parser.add_argument("--top-k", type=str, default=",".join(str(x) for x in DEFAULT_TOP_K))
    args = parser.parse_args()

    if args.dataset == "v3" and not args.joint3:
        args.joint3 = True

    if not (args.build_cache or args.grid or args.all):
        parser.error("Specify --build-cache, --grid, or --all")

    p = paths_for(args.dataset)
    dataset = load_dataset(args.dataset)

    if args.dataset == "v3":
        anchor_ks = parse_int_list(args.anchor_k) if args.anchor_k else DEFAULT_ANCHOR_K_V3
        epsilons = parse_float_list(args.epsilons) if args.epsilons else DEFAULT_EPS_V3
        top_ks = parse_int_list(args.top_k) if args.top_k else DEFAULT_TOP_K
    else:
        anchor_ks = (
            parse_int_list(args.anchor_k)
            if args.anchor_k
            else (DEFAULT_ANCHOR_K_V2 if args.dataset == "v2" else DEFAULT_ANCHOR_K_V1)
        )
        thresholds = (
            parse_float_list(args.thresholds)
            if args.thresholds
            else (DEFAULT_THRESHOLD_V2 if args.dataset == "v2" else DEFAULT_THRESHOLD_V1)
        )
        epsilons = parse_float_list(args.epsilons) if args.epsilons else DEFAULT_EPS
        top_ks = parse_int_list(args.top_k)

    if args.build_cache or args.all:
        build_embedding_cache(
            dataset, p["embeddings"],
            dataset_version=args.dataset,
            kb_path=p.get("kb"),
        )

    if args.grid or args.all:
        entries, query_vectors = load_embedding_cache(
            dataset, p["embeddings"],
            dataset_version=args.dataset,
            kb_path=p.get("kb"),
        )
        if args.dataset == "v3" and args.joint3:
            results = run_grid_joint3(
                entries, query_vectors, dataset,
                epsilons, anchor_ks, top_ks, args.fixed_threshold,
                p["grid"], args.fpr_max,
            )
        else:
            results = run_grid(
                entries, query_vectors, dataset,
                epsilons, anchor_ks, thresholds, top_ks,
                args.dataset, p["grid"], args.fpr_max,
            )
        top = select_top_configs(results, p["top5"], args.dataset, args.select_top, args.fpr_max)
        logger.info("Best: %s", json.dumps(top[0], ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
