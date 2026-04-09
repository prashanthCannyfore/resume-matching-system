from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Using SQLite for smooth development (no password hassle)
    DATABASE_URL: str = "sqlite+aiosqlite:///./rms.db"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()