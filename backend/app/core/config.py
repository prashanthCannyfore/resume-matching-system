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
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ================== DATABASE ==================
    DATABASE_URL: str
    DATABASE_SSL_MODE: str = "disable"

    # ================== OLLAMA (replaces OpenAI / Gemini / Grok) ==================
    # Base URL of your Ollama server
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # LLM used for insights, parsing, summarisation
    # Recommended: llama3.2:3b (fast/CPU), qwen2.5:7b (better quality, needs GPU)
    OLLAMA_LLM_MODEL: str = "llama3.2:3b"

    # Embedding model — nomic-embed-text produces 768-dim vectors
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # Inference settings
    OLLAMA_TIMEOUT: float = 120.0          # seconds per request
    OLLAMA_CONTEXT_LENGTH: int = 4096      # num_ctx passed to Ollama
    OLLAMA_EMBED_CONCURRENCY: int = 4      # max parallel embed calls

    # Legacy API keys — kept so existing .env files don't break; no longer used
    GROQ_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    def get_allowed_origins(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS


# Create settings instance
settings = Settings()
