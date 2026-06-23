from pydantic_settings import BaseSettings
# lru_cache removed for hot-reload support
from pathlib import Path

# Project root is two levels up from this file (backend/app/config.py)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/opswarden"
    SECRET_KEY: str = "YOUR_SECRET_KEY_CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Ollama LLM (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    OLLAMA_TEMPERATURE: float = 0.1
    OLLAMA_MAX_TOKENS: int = 800
    OLLAMA_TIMEOUT: float = 60.0
    

    # RAG
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    RAG_SCORE_THRESHOLD: float = 0.65
    RAG_TOP_K: int = 3
    RAG_ANCHOR_TOP_K: int = 8
    ANCHOR_QUANT_EPSILON: float = 0.02

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


# @lru_cache() removed for hot-reload support
def get_settings():
    return Settings()