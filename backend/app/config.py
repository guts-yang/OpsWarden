from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Project root is two levels up from this file (backend/app/config.py)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:342802@localhost:3306/opswarden?charset=utf8mb4"
    SECRET_KEY: str = "ops-warden-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # DeepSeek LLM
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_TEMPERATURE: float = 0.1
    DEEPSEEK_MAX_TOKENS: int = 800
    DEEPSEEK_TIMEOUT: float = 30.0

    # ChromaDB & RAG
    CHROMA_PATH: str = "./chroma_db"
    CHROMA_COLLECTION: str = "ops_faq"
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    RAG_SCORE_THRESHOLD: float = 0.4
    RAG_TOP_K: int = 3

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()