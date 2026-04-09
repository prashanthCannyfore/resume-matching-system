from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.schemas.job import JobCreate
from app.api.services.job_service import create_job

router = APIRouter()

@router.post("/")
async def create_job_api(
    job: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    return await create_job(job, db)