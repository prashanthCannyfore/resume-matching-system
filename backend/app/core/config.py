from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application Settings
    DEBUG: bool = True
    API_TITLE: str = "Resume Matching System (RMS)"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = "AI-Powered Resume & Job Matching Platform"
    TESSERACT_CMD: str | None = None
    # Security & CORS
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env

    def get_allowed_origins(self) -> List[str]:
        """Support comma-separated string from .env"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS


# Create settings instance
settings = Settings()
