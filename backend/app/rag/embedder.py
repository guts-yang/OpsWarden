import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

_model = None

# BGE 模型官方推荐：查询文本加此前缀，文档文本不加
_QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE)
        logger.info("Embedding model loaded")
    return _model


def embed_query(text: str) -> list[float]:
    """Encode query text with retrieval instruction prefix (for search)."""
    return _get_model().encode(
        _QUERY_INSTRUCTION + text, normalize_embeddings=True
    ).tolist()


def embed_document(text: str) -> list[float]:
    """Encode document text without instruction prefix (for indexing)."""
    return _get_model().encode(text, normalize_embeddings=True).tolist()
