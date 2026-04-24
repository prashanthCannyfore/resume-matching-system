from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.services.job_service import process_job_description, create_job
from app.api.schemas.job import JobCreate

router = APIRouter()


@router.post("/")
async def create_job_api(
    job: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    return await create_job(job, db)


@router.post("/upload")
async def upload_job(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await process_job_description(file, db)
