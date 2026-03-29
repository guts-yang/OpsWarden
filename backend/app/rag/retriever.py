import logging
from app.config import get_settings
from app.rag.chroma_client import get_collection
from app.rag.embedder import embed

logger = logging.getLogger(__name__)


def search(query: str, top_k: int = None, threshold: float = None) -> list[dict]:
    settings = get_settings()
    if top_k is None:
        top_k = settings.RAG_TOP_K
    if threshold is None:
        threshold = settings.RAG_SCORE_THRESHOLD

    try:
        collection = get_collection()
        total = collection.count()
        if total == 0:
            return []

        query_embedding = embed(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, total),
        )

        docs = []
        for doc_id, distance, metadata in zip(
            results["ids"][0],
            results["distances"][0],
            results["metadatas"][0],
        ):
            if distance < threshold:
                docs.append({
                    "id": int(doc_id),
                    "question": metadata.get("question", ""),
                    "solution": metadata.get("solution", ""),
                    "category": metadata.get("category", ""),
                    "score": round(1 - distance, 4),
                })
        return docs
    except Exception as e:
        logger.warning(f"ChromaDB search error: {e}")
        return []


def add_entry(entry_id: int, question: str, solution: str, category: str):
    collection = get_collection()
    text = f"{question} {solution}"
    embedding = embed(text)
    collection.upsert(
        ids=[str(entry_id)],
        embeddings=[embedding],
        metadatas=[{"question": question, "solution": solution, "category": category}],
        documents=[text],
    )


def delete_entry(entry_id: int):
    collection = get_collection()
    collection.delete(ids=[str(entry_id)])


def collection_count() -> int:
    try:
        return get_collection().count()
    except Exception:
        return -1
