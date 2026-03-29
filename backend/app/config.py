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
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()