from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://tiara:tiara_password@localhost:5432/tiara_db"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-minimum-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CAREGIVER_DASHBOARD_TOKEN_EXPIRE_MINUTES: int = 30

    # Media storage
    MEDIA_STORAGE_PATH: str = "./media_storage"

    # AI / STT
    WHISPER_MODEL_SIZE: str = "base"

    # LLM
    LLM_PROVIDER: str = "none"  # none | openai | anthropic | gemini
    LLM_API_KEY: Optional[str] = None

    # CORS
    # Comma-separated origins, for example:
    # https://tiaracare.my.id,https://www.tiaracare.my.id,http://localhost:3000
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # App
    APP_NAME: str = "TIARA API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
