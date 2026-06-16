from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Project root is two levels up from this file (backend/app/config.py)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/opswarden"
    SECRET_KEY: str = "ops-warden-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # DeepSeek LLM（本地部署，OpenAI 兼容接口；后端请求 {BASE_URL}/chat/completions）
    # 本地服务（Ollama / vLLM / LM Studio 等）通常不校验 Key，默认填占位符即可
    DEEPSEEK_API_KEY: str = "local"
    DEEPSEEK_BASE_URL: str = "http://localhost:11434/v1"
    DEEPSEEK_MODEL: str = "deepseek-r1"
    DEEPSEEK_TEMPERATURE: float = 0.1
    DEEPSEEK_MAX_TOKENS: int = 800
    DEEPSEEK_TIMEOUT: float = 30.0

    # RAG（取值来自 docs/rag_hyperparam_report_v3_joint.md 联合调优结论）
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    RAG_SCORE_THRESHOLD: float = 0.65
    RAG_TOP_K: int = 3
    RAG_ANCHOR_TOP_K: int = 8
    ANCHOR_QUANT_EPSILON: float = 0.02

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()