from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base

# Import routers
from app.api.routers import router as main_router
from app.api.routers.vector_router import router as vector_router

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    debug=settings.DEBUG,
)

# ====================== CORS (Secure Configuration) ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ========================================================================

app.include_router(main_router, prefix="/api")
app.include_router(vector_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "✅ Resume Matching System API is running successfully with PostgreSQL + Persistent FAISS!"
    }


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ PostgreSQL tables created / migrated successfully")