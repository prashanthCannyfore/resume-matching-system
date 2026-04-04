"""
Application configuration module.
Manages environment variables and application settings.
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./resume_matching.db"
    
    # API Metadata
    api_title: str = "Resume Matching System"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered resume matching using RAG + filtering"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"
    
    # Application
    debug: bool = True
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
