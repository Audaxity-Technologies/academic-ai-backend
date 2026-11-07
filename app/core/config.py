from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Academic AI API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    CORS_ORIGINS: list[str] = ["*", "http://localhost:5173", "http://127.0.0.1:5173"]

    SYLLABUS_TOP_K: int = Field(default=10, ge=1, le=40)
    SYLLABUS_CHUNK_SIZE: int = Field(default=1800, ge=200, le=6000)

    # Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change_me")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()