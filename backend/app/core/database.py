from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# =========================
# POSTGRESQL ASYNC ENGINE
# =========================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_timeout=30,
    # Fix for SSL / self-signed certificate issues
    connect_args={"ssl": None}
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