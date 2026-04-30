# app/api/routers/vector_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.services.vector_store import rebuild_faiss_from_db

router = APIRouter(prefix="/vector", tags=["Vector Store"])

@router.post("/rebuild")
async def rebuild_vector_store(db: AsyncSession = Depends(get_db)):
    """Rebuild FAISS index from all candidates in database"""
    result = await rebuild_faiss_from_db(db)
    return result