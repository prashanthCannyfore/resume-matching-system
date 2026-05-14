import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base

# Import routers
from app.api.routers import router as main_router
from app.api.routers.vector_router import router as vector_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix="/api")
app.include_router(vector_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "✅ Resume Matching System API is running (Ollama-powered, fully local)"
    }


@app.get("/health")
async def health():
    from app.api.services.ollama_client import check_ollama_health
    ollama_ok = await check_ollama_health()
    return {
        "api": "ok",
        "ollama": "ok" if ollama_ok else "unreachable",
        "llm_model": settings.OLLAMA_LLM_MODEL,
        "embed_model": settings.OLLAMA_EMBED_MODEL,
        "ollama_url": settings.OLLAMA_BASE_URL,
    }


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ PostgreSQL tables created / migrated successfully")

    from app.api.services.ollama_client import check_ollama_health
    if await check_ollama_health():
        logger.info(f"✅ Ollama reachable at {settings.OLLAMA_BASE_URL} | LLM={settings.OLLAMA_LLM_MODEL} | Embed={settings.OLLAMA_EMBED_MODEL}")
    else:
        logger.warning(
            f"⚠️  Ollama NOT reachable at {settings.OLLAMA_BASE_URL}. "
            "Resume parsing and matching will use fallback logic until Ollama is running."
        )