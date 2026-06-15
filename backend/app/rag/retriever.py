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


def _compute_quality_score(qv: np.ndarray, sv: np.ndarray) -> float:
    """自检质量分：question 向量 与 solution 向量 的余弦相似度，clip 到 [0, 1]。

    BGE 模型输出已 L2 归一化（embedder.embed_document 中 normalize_embeddings=True），
    因此点积即余弦相似度；负值 clip 为 0，超过 1 的浮点误差 clip 为 1。
    """
    try:
        sim = float(np.dot(qv, sv))
    except Exception:
        return 0.0
    if not np.isfinite(sim):
        return 0.0
    if sim < 0.0:
        return 0.0
    if sim > 1.0:
        return 1.0
    return sim


def ingest_kb_entry(
    db: Session,
    entry_id: int,
    question: str,
    solution: str,
    category: str,
    doc_id: str,
    page_index: int,
) -> None:
    """写入切片向量：量化锚点 upsert + 条目 embedding / anchor_id / doc 元数据 / 自检质量分。

    自检质量分 (match_score)：
      分别对 question 与 solution 做 embedding，二者余弦相似度即为 match_score，
      反映「问题-解决方案对的内在语义一致性」，与实际 RAG 检索命中率无关。
    整体 entry.embedding：
      使用 (qv + sv) / 2 再 L2 归一化的「联合表示」，与现有量化锚点流程兼容，
      避免重复调用模型。
    """
    settings = get_settings()
    eps = settings.ANCHOR_QUANT_EPSILON

    q_text = (question or "").strip()
    s_text = (solution or "").strip()

    quality_score = 0.0
    if q_text and s_text:
        try:
            qv = np.asarray(embed_document(q_text), dtype=np.float64)
            sv = np.asarray(embed_document(s_text), dtype=np.float64)
            quality_score = _compute_quality_score(qv, sv)
            joint = (qv + sv) / 2.0
            jn = float(np.linalg.norm(joint)) + 1e-12
            joint = joint / jn
            raw = joint.astype(float).tolist()
        except Exception as ex:
            logger.warning(f"quality score / joint embed failed for entry {entry_id}: {ex}")
            raw = embed_document(f"{q_text} {s_text}")
    else:
        logger.warning(f"entry {entry_id} has empty question/solution, quality_score=0.0")
        raw = embed_document(f"{q_text} {s_text}".strip() or " ")

    quantized = quantize_vector(raw, eps)
    q_list = quantized.astype(float).tolist()
    aid = _get_or_create_anchor(db, q_list)
    db.execute(
        sql_update(KBEntry)
        .where(KBEntry.id == entry_id)
        .values(
            anchor_id=aid,
            embedding=raw,
            doc_id=doc_id,
            page_index=page_index,
            match_score=round(quality_score, 4),
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


def collection_count() -> int:
    try:
        with SessionLocal() as db:
            return db.query(KBEntry).filter(KBEntry.embedding.isnot(None)).count()
    except Exception:
        return -1
