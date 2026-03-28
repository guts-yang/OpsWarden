from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://ops:ops123456@localhost:3306/opswarden?charset=utf8mb4"
    SECRET_KEY: str = "ops-warden-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()