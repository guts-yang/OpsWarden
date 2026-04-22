import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import update as sql_update
import numpy as np

from app.config import get_settings
from app.database import SessionLocal
from app.models.knowledge import KBAnchor, KBEntry
from app.rag.embedder import embed_query, embed_document
from app.rag.quantizer import quantize_vector, quant_key_from_vector

logger = logging.getLogger(__name__)


def _get_or_create_anchor(db: Session, quantized_list: list[float]) -> int:
    """quantized_list 与 anchor_vec 存储一致顺序。"""
    q_arr = np.asarray(quantized_list, dtype=np.float64)
    qk = quant_key_from_vector(q_arr)
    row = db.query(KBAnchor).filter(KBAnchor.quant_key == qk).first()
    if row:
        return int(row.id)
    anchor = KBAnchor(
        quant_key=qk,
        anchor_vec=quantized_list,
    )
    db.add(anchor)
    db.flush()
    return int(anchor.id)


def ingest_kb_entry(
    db: Session,
    entry_id: int,
    question: str,
    solution: str,
    category: str,
    doc_id: str,
    page_index: int,
) -> None:
    """写入切片向量：量化锚点 upsert + 条目 embedding / anchor_id / doc 元数据。"""
    settings = get_settings()
    eps = settings.ANCHOR_QUANT_EPSILON
    raw = embed_document(f"{question} {solution}")
    qv = quantize_vector(raw, eps)
    q_list = qv.astype(float).tolist()
    aid = _get_or_create_anchor(db, q_list)
    db.execute(
        sql_update(KBEntry)
        .where(KBEntry.id == entry_id)
        .values(
            anchor_id=aid,
            embedding=raw,
            doc_id=doc_id,
            page_index=page_index,
        )
    )


def prune_anchor_if_unused(db: Session, anchor_id: int | None) -> None:
    if anchor_id is None:
        return
    n = db.query(KBEntry).filter(KBEntry.anchor_id == anchor_id).count()
    if n == 0:
        db.query(KBAnchor).filter(KBAnchor.id == anchor_id).delete()
        db.flush()


def search(query: str, top_k: int | None = None, threshold: float | None = None) -> list[dict]:
    settings = get_settings()
    if top_k is None:
        top_k = settings.RAG_TOP_K
    if threshold is None:
        threshold = settings.RAG_SCORE_THRESHOLD
    anchor_k = settings.RAG_ANCHOR_TOP_K

    try:
        qvec = embed_query(query)
        q = np.asarray(qvec, dtype=np.float64)
        qn = float(np.linalg.norm(q)) + 1e-12

        with SessionLocal() as db:
            acnt = db.query(KBAnchor).count()
            if acnt == 0:
                return []

            distance_expr = KBAnchor.anchor_vec.cosine_distance(qvec)
            anchor_rows = db.execute(
                select(KBAnchor, (1 - distance_expr).label("ascore"))
                .order_by(distance_expr)
                .limit(anchor_k)
            ).all()

            anchor_ids = [int(r.KBAnchor.id) for r in anchor_rows]
            if not anchor_ids:
                return []

            entries = (
                db.query(KBEntry)
                .filter(
                    KBEntry.anchor_id.in_(anchor_ids),
                    KBEntry.embedding.isnot(None),
                )
                .all()
            )

        scored: list[tuple[KBEntry, float]] = []
        for e in entries:
            ev = np.asarray(e.embedding, dtype=np.float64)
            en = float(np.linalg.norm(ev)) + 1e-12
            score = float(np.dot(q, ev) / (qn * en))
            if score >= threshold:
                scored.append((e, score))

        scored.sort(key=lambda x: -x[1])
        out = []
        for e, sc in scored[:top_k]:
            out.append({
                "id": e.id,
                "question": e.question,
                "solution": e.solution,
                "category": e.category,
                "score": round(sc, 4),
            })
        return out
    except Exception as ex:
        logger.warning(f"RAG search error: {ex}")
        return []


def delete_entry_embed_only(entry_id: int):
    """兼容旧名：已由行删除代替；保留空实现避免误调用。"""
    logger.debug("delete_entry_embed_only noop for entry_id=%s", entry_id)


def collection_count() -> int:
    try:
        with SessionLocal() as db:
            return db.query(KBEntry).filter(KBEntry.embedding.isnot(None)).count()
    except Exception:
        return -1
