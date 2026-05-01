# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application Settings
    DEBUG: bool = True
    API_TITLE: str = "Resume Matching System (RMS)"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = "AI-Powered Resume & Job Matching Platform"
    TESSERACT_CMD: str | None = None

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vue default port (Vite)
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

    # ================== DATABASE ==================
    # Now properly loaded from .env (no hard-coded fallback)
    DATABASE_URL: str

    # Optional API Keys
    GROQ_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore any extra variables in .env

    def get_allowed_origins(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS


# Create settings instance
settings = Settings()
