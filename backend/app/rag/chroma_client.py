import chromadb
import logging
from functools import lru_cache
from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_collection():
    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"ChromaDB collection '{settings.CHROMA_COLLECTION}' loaded, docs: {collection.count()}")
    return collection
