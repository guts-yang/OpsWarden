#!/usr/bin/env python3
"""Verify top RAG hyperparameter configs against live PostgreSQL + pgvector.

Usage (from repo root, PostgreSQL must be running):
    python scripts/rag_hyperparam_verify_db.py --dataset v2
    python scripts/rag_hyperparam_verify_db.py --dataset v3 --joint3
    python scripts/rag_hyperparam_verify_db.py --dataset v1
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

os.environ.pop("CURL_CA_BUNDLE", None)
os.environ.pop("REQUESTS_CA_BUNDLE", None)

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
SCRIPTS = ROOT / "scripts"
CACHE_DIR = SCRIPTS / ".eval_cache"
FAQ_DOC_ID = "OpsWarden_FAQ"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rag_hyperparam_verify_db")


def paths_for(dataset_version: str) -> dict[str, Path]:
    if dataset_version == "v3":
        return {
            "dataset": SCRIPTS / "eval_datasets" / "faq_eval_v3.json",
            "configs": CACHE_DIR / "top5_configs_v3_joint.json",
            "verify": CACHE_DIR / "db_verify_results_v3_joint.json",
        }
    if dataset_version == "v2":
        return {
            "dataset": SCRIPTS / "eval_datasets" / "faq_eval_v2.json",
            "configs": CACHE_DIR / "top5_configs_v2.json",
            "verify": CACHE_DIR / "db_verify_results_v2.json",
        }
    return {
        "dataset": SCRIPTS / "eval_datasets" / "faq_exact.json",
        "configs": CACHE_DIR / "top5_configs.json",
        "verify": CACHE_DIR / "db_verify_results.json",
    }


def _apply_env(epsilon: float, anchor_k: int, threshold: float, top_k: int) -> None:
    os.environ["ANCHOR_QUANT_EPSILON"] = str(epsilon)
    os.environ["RAG_ANCHOR_TOP_K"] = str(anchor_k)
    os.environ["RAG_SCORE_THRESHOLD"] = str(threshold)
    os.environ["RAG_TOP_K"] = str(top_k)
    from app.config import get_settings

    get_settings.cache_clear()


def _reingest_faq(epsilon: float) -> int:
    from sqlalchemy import text

    from app.config import get_settings
    from app.database import SessionLocal
    from app.models.knowledge import KBAnchor, KBEntry
    from app.rag.faq_loader import FAQ_PATH, _parse_faq
    from app.rag.retriever import ingest_kb_entry, prune_anchor_if_unused

    get_settings.cache_clear()
    eps = get_settings().ANCHOR_QUANT_EPSILON
    if abs(eps - epsilon) > 1e-9:
        raise RuntimeError(f"Settings epsilon mismatch: expected {epsilon}, got {eps}")

    parsed = _parse_faq(FAQ_PATH.read_text(encoding="utf-8"))
    with SessionLocal() as db:
        faq_rows = db.query(KBEntry).filter(KBEntry.doc_id == FAQ_DOC_ID).all()
        anchor_ids = {r.anchor_id for r in faq_rows if r.anchor_id is not None}
        db.execute(text("DELETE FROM kb_entries WHERE doc_id = :doc_id"), {"doc_id": FAQ_DOC_ID})
        db.commit()
        for aid in anchor_ids:
            prune_anchor_if_unused(db, aid)
        db.commit()

        db_entries = []
        for item in parsed:
            obj = KBEntry(
                category=item["category"],
                question=item["question"],
                solution=item["solution"],
                source="manual",
            )
            db.add(obj)
            db_entries.append(obj)
        db.flush()

        for idx, obj in enumerate(db_entries, start=1):
            ingest_kb_entry(db, obj.id, obj.question, obj.solution, obj.category, FAQ_DOC_ID, idx)
        db.commit()
        n = db.query(KBEntry).filter(KBEntry.doc_id == FAQ_DOC_ID).count()
        n_anchors = db.query(KBAnchor).count()
        logger.info("Re-ingested FAQ: %d entries, %d anchors (eps=%.2f)", n, n_anchors, epsilon)
        return n


def _top_score(query: str, anchor_k: int) -> float:
    from app.rag.retriever import search

    hits = search(query, top_k=1, threshold=0.0, anchor_k=anchor_k)
    return float(hits[0]["score"]) if hits else 0.0


def _evaluate_db_config_v1(cfg: dict, dataset: list[dict]) -> dict:
    from app.rag.retriever import search

    epsilon = float(cfg["epsilon"])
    anchor_k = int(cfg["anchor_k"])
    threshold = float(cfg["threshold"])
    top_k = int(cfg["top_k"])

    _apply_env(epsilon, anchor_k, threshold, top_k)
    _reingest_faq(epsilon)

    hit1_thresh = hit1_raw = 0
    for item in dataset:
        expected = int(item["page_index"])
        query = item["query"]
        all_hits = search(query, top_k=1, threshold=0.0, anchor_k=anchor_k)
        thresh_hits = search(query, top_k=top_k, threshold=threshold, anchor_k=anchor_k)
        if all_hits and all_hits[0].get("page_index") == expected:
            hit1_raw += 1
        if thresh_hits and thresh_hits[0].get("page_index") == expected:
            hit1_thresh += 1

    n = len(dataset)
    return {
        "rank": cfg.get("rank"),
        "epsilon": epsilon,
        "anchor_k": anchor_k,
        "threshold": threshold,
        "top_k": top_k,
        "memory_hit1_with_threshold": float(cfg.get("hit1_with_threshold", 0)),
        "db_hit1_with_threshold": hit1_thresh / n,
        "db_hit1_no_threshold": hit1_raw / n,
        "delta_hit1": hit1_thresh / n - float(cfg.get("hit1_with_threshold", 0)),
    }


def _evaluate_db_config_v2(cfg: dict, dataset: list[dict]) -> dict:
    from app.rag.retriever import search

    epsilon = float(cfg["epsilon"])
    anchor_k = int(cfg["anchor_k"])
    threshold = float(cfg["threshold"])
    top_k = int(cfg["top_k"])

    _apply_env(epsilon, anchor_k, threshold, top_k)
    _reingest_faq(epsilon)

    exact_hit = para_hit = exact_n = para_n = neg_n = neg_fp = 0

    for item in dataset:
        split = item.get("split", "exact")
        query = item["query"]
        if split in ("exact", "paraphrase"):
            expected = int(item["page_index"])
            hits = search(query, top_k=top_k, threshold=threshold, anchor_k=anchor_k)
            ok = bool(hits and hits[0].get("page_index") == expected)
            if split == "exact":
                exact_n += 1
                exact_hit += int(ok)
            else:
                para_n += 1
                para_hit += int(ok)
        elif split == "negative":
            neg_n += 1
            if _top_score(query, anchor_k) >= threshold:
                neg_fp += 1

    return {
        "rank": cfg.get("rank"),
        "epsilon": epsilon,
        "anchor_k": anchor_k,
        "threshold": threshold,
        "top_k": top_k,
        "memory_hit1_exact": float(cfg.get("hit1_exact", 0)),
        "memory_hit1_para": float(cfg.get("hit1_para", 0)),
        "memory_fpr": float(cfg.get("fpr", 0)),
        "db_hit1_exact": exact_hit / exact_n if exact_n else 0.0,
        "db_hit1_para": para_hit / para_n if para_n else 0.0,
        "db_fpr": neg_fp / neg_n if neg_n else 0.0,
        "delta_hit1_para": (para_hit / para_n if para_n else 0.0) - float(cfg.get("hit1_para", 0)),
        "delta_fpr": (neg_fp / neg_n if neg_n else 0.0) - float(cfg.get("fpr", 0)),
    }


def _evaluate_db_config_v3(cfg: dict, dataset: list[dict]) -> dict:
    """Dual-track verify: canonical exact queries via DB; full v3 via in-memory."""
    from app.rag.eval_engine import (
        EvalEntry,
        build_anchors,
        compute_joint_embedding,
        l1_anchor_hit,
        rank_all_candidates,
        search_inmemory,
    )
    from app.rag.embedder import embed_document, embed_query
    from app.rag.retriever import search
    import numpy as np

    epsilon = float(cfg["epsilon"])
    anchor_k = int(cfg["anchor_k"])
    threshold = float(cfg["threshold"])
    top_k = int(cfg["top_k"])

    _apply_env(epsilon, anchor_k, threshold, top_k)
    _reingest_faq(epsilon)

    exact_hit = exact_n = 0
    for item in dataset:
        if item.get("split") != "exact":
            continue
        expected = int(item["page_index"])
        hits = search(item["query"], top_k=top_k, threshold=threshold, anchor_k=anchor_k)
        ok = bool(hits and hits[0].get("page_index") == expected)
        exact_n += 1
        exact_hit += int(ok)

    kb_path = SCRIPTS / "eval_datasets" / "faq_eval_kb_v3.json"
    emb_cache = CACHE_DIR / "faq_eval_v3_embeddings.npz"
    entries: list[EvalEntry] = []
    if emb_cache.exists():
        data = __import__("numpy").load(emb_cache, allow_pickle=True)
        for i in range(len(data["page_index"])):
            entries.append(
                EvalEntry(
                    page_index=int(data["page_index"][i]),
                    question=str(data["questions"][i]),
                    solution=str(data["solutions"][i]),
                    category=str(data["categories"][i]),
                    embedding=np.asarray(data["joint_embeddings"][i], dtype=np.float64),
                )
            )
    else:
        kb_rows = json.loads(kb_path.read_text(encoding="utf-8"))
        for row in kb_rows:
            qv = np.asarray(embed_document(row["question"].strip()), dtype=np.float64)
            sv = np.asarray(embed_document(row["solution"].strip()), dtype=np.float64)
            entries.append(
                EvalEntry(
                    page_index=int(row["page_index"]),
                    question=row["question"].strip(),
                    solution=row["solution"].strip(),
                    category=row["category"],
                    embedding=compute_joint_embedding(qv, sv),
                )
            )
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

    para_hit = para_n = hard_hit = hard_n = neg_n = neg_fp = 0
    l1_hard_hit = hard_n_l1 = recall_at_k_para_hit = 0

    for item in dataset:
        split = item.get("split", "exact")
        if split == "exact":
            continue
        qvec = np.asarray(embed_query(item["query"]), dtype=np.float64)
        ranked, l1_idx = rank_all_candidates(qvec, eval_entries, anchors, anchor_k=anchor_k)
        hits, _ = search_inmemory(
            qvec, eval_entries, anchors, anchor_k=anchor_k, threshold=threshold, top_k=top_k
        )
        if split in ("paraphrase", "hard_confusion"):
            expected = int(item["page_index"])
            hit_ok = bool(hits and hits[0]["page_index"] == expected)
            if split == "paraphrase":
                para_n += 1
                para_hit += int(hit_ok)
                if expected in {h["page_index"] for h in hits}:
                    recall_at_k_para_hit += 1
            else:
                hard_n += 1
                hard_hit += int(hit_ok)
                if l1_anchor_hit(eval_entries, anchors, expected, l1_idx):
                    l1_hard_hit += 1
                hard_n_l1 += 1
        elif split == "negative":
            neg_n += 1
            top_score = ranked[0][1] if ranked else 0.0
            if top_score >= threshold:
                neg_fp += 1

    mem_para = float(cfg.get("hit1_para", 0))
    mem_hard = float(cfg.get("hit1_hard", 0))
    mem_fpr = float(cfg.get("fpr", 0))
    db_para = para_hit / para_n if para_n else 0.0
    db_hard = hard_hit / hard_n if hard_n else 0.0
    db_fpr = neg_fp / neg_n if neg_n else 0.0

    return {
        "rank": cfg.get("rank"),
        "epsilon": epsilon,
        "anchor_k": anchor_k,
        "threshold": threshold,
        "top_k": top_k,
        "verify_mode": "db_exact + memory_full_kb",
        "memory_hit1_exact": float(cfg.get("hit1_exact", 0)),
        "memory_hit1_para": mem_para,
        "memory_hit1_hard": mem_hard,
        "memory_fpr": mem_fpr,
        "memory_l1_recall_hard": float(cfg.get("l1_recall_hard", 0)),
        "memory_recall_at_k_para": float(cfg.get("recall_at_k_para", 0)),
        "db_hit1_exact": exact_hit / exact_n if exact_n else 0.0,
        "db_hit1_para": db_para,
        "db_hit1_hard": db_hard,
        "db_fpr": db_fpr,
        "db_l1_recall_hard": l1_hard_hit / hard_n_l1 if hard_n_l1 else 0.0,
        "db_recall_at_k_para": recall_at_k_para_hit / para_n if para_n else 0.0,
        "delta_hit1_para": db_para - mem_para,
        "delta_hit1_hard": db_hard - mem_hard,
        "delta_fpr": db_fpr - mem_fpr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify top configs on live PostgreSQL")
    parser.add_argument("--dataset", choices=["v1", "v2", "v3"], default="v2")
    parser.add_argument("--joint3", action="store_true")
    parser.add_argument("--configs", type=str, default="")
    args = parser.parse_args()

    if args.dataset == "v3" and not args.joint3:
        args.joint3 = True

    p = paths_for(args.dataset)
    configs_path = Path(args.configs) if args.configs else p["configs"]
    if not configs_path.exists():
        logger.error("Configs not found: %s", configs_path)
        return 1
    if not p["dataset"].exists():
        logger.error("Dataset not found: %s", p["dataset"])
        return 1

    configs = json.loads(configs_path.read_text(encoding="utf-8"))
    dataset = json.loads(p["dataset"].read_text(encoding="utf-8"))

    from app.database import SessionLocal

    try:
        with SessionLocal() as db:
            db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as ex:
        logger.error("Database unavailable: %s", ex)
        return 1

    if args.dataset == "v3":
        eval_fn = _evaluate_db_config_v3
    elif args.dataset == "v2":
        eval_fn = _evaluate_db_config_v2
    else:
        eval_fn = _evaluate_db_config_v1
    results: list[dict] = []
    started = time.time()

    for cfg in configs:
        logger.info(
            "Verifying rank=%s eps=%.2f ak=%d th=%.2f tk=%d",
            cfg.get("rank"), cfg["epsilon"], cfg["anchor_k"], cfg["threshold"], cfg["top_k"],
        )
        try:
            row = eval_fn(cfg, dataset)
            results.append(row)
            if args.dataset == "v3":
                logger.info(
                    "  para mem=%.3f db=%.3f | hard mem=%.3f db=%.3f | fpr mem=%.3f db=%.3f",
                    row["memory_hit1_para"], row["db_hit1_para"],
                    row["memory_hit1_hard"], row["db_hit1_hard"],
                    row["memory_fpr"], row["db_fpr"],
                )
            elif args.dataset == "v2":
                logger.info(
                    "  para mem=%.3f db=%.3f | fpr mem=%.3f db=%.3f",
                    row["memory_hit1_para"], row["db_hit1_para"],
                    row["memory_fpr"], row["db_fpr"],
                )
            else:
                logger.info(
                    "  memory=%.3f db=%.3f delta=%+.3f",
                    row["memory_hit1_with_threshold"], row["db_hit1_with_threshold"], row["delta_hit1"],
                )
        except Exception as ex:
            logger.exception("Verify failed: %s", ex)
            results.append({"error": str(ex), **cfg})

    p["verify"].write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved to %s (%.1fs)", p["verify"], time.time() - started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
