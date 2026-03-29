import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE)
        logger.info("Embedding model loaded")
    return _model


def embed(text: str) -> list[float]:
    return _get_model().encode(text, normalize_embeddings=True).tolist()
