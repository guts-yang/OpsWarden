import logging
import os
from app.config import get_settings

logger = logging.getLogger(__name__)

_model = None

# 设置离线模式，禁止连接 HuggingFace
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# BGE 模型本地缓存路径
_LOCAL_MODEL_PATH = "/root/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5/snapshots/default"

# BGE 模型官方推荐：查询文本加此前缀，文档文本不加
_QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        settings = get_settings()
        logger.info(f"Loading embedding model from local path: {_LOCAL_MODEL_PATH}")
        _model = SentenceTransformer(_LOCAL_MODEL_PATH, device=settings.EMBEDDING_DEVICE)
        logger.info("Embedding model loaded from local cache")
    return _model


def embed_query(text: str) -> list[float]:
    """Encode query text with retrieval instruction prefix (for search)."""
    return _get_model().encode(
        _QUERY_INSTRUCTION + text, normalize_embeddings=True
    ).tolist()


def embed_document(text: str) -> list[float]:
    """Encode document text without instruction prefix (for indexing)."""
    return _get_model().encode(text, normalize_embeddings=True).tolist()
