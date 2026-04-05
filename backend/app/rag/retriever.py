import logging
from sqlalchemy import select, update
from pgvector.sqlalchemy import Vector
from app.config import get_settings
from app.database import SessionLocal
from app.models.knowledge import KBEntry
from app.rag.embedder import embed_query, embed_document

logger = logging.getLogger(__name__)


def search(query: str, top_k: int = None, threshold: float = None) -> list[dict]:
    settings = get_settings()
    if top_k is None:
        top_k = settings.RAG_TOP_K
    if threshold is None:
        threshold = settings.RAG_SCORE_THRESHOLD

    try:
        vec = embed_query(query)
        with SessionLocal() as db:
            total = db.query(KBEntry).filter(KBEntry.embedding.isnot(None)).count()
            if total == 0:
                return []

            # cosine_distance returns 0=identical, 2=opposite; score = 1 - distance
            distance_expr = KBEntry.embedding.cosine_distance(vec)
            rows = db.execute(
                select(KBEntry, (1 - distance_expr).label("score"))
                .where(KBEntry.embedding.isnot(None))
                .order_by(distance_expr)
                .limit(top_k)
            ).all()

        return [
            {
                "id": row.KBEntry.id,
                "question": row.KBEntry.question,
                "solution": row.KBEntry.solution,
                "category": row.KBEntry.category,
                "score": round(float(row.score), 4),
            }
            for row in rows
            if float(row.score) >= threshold
        ]
    except Exception as e:
        logger.warning(f"pgvector search error: {e}")
        return []


def add_entry(entry_id: int, question: str, solution: str, category: str):
    vec = embed_document(f"{question} {solution}")
    with SessionLocal() as db:
        db.execute(
            update(KBEntry).where(KBEntry.id == entry_id).values(embedding=vec)
        )
        db.commit()


def delete_entry(entry_id: int):
    with SessionLocal() as db:
        db.execute(
            update(KBEntry).where(KBEntry.id == entry_id).values(embedding=None)
        )
        db.commit()


def collection_count() -> int:
    try:
        with SessionLocal() as db:
            return db.query(KBEntry).filter(KBEntry.embedding.isnot(None)).count()
    except Exception:
        return -1
