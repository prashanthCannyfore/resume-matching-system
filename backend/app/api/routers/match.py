from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.services.matching_service import match_candidates

router = APIRouter()


@router.get("/job/{job_id}")
async def match(job_id: int, db: AsyncSession = Depends(get_db)):
    return await match_candidates(job_id, db)
