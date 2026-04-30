# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os
from app.core.config import settings

# =========================
# POSTGRESQL ASYNC ENGINE
# =========================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Prevents stale connections
    pool_timeout=30,
)

# =========================
# ASYNC SESSION
# =========================
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =========================
# BASE MODEL
# =========================
class Base(DeclarativeBase):
    pass


# =========================
# DB DEPENDENCY
# =========================
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
