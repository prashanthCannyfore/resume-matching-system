from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.services.job_service import process_job_description, create_job
from app.api.schemas.job import JobCreate
from app.api.services.matching_service import match_candidates

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


@router.post("/{job_id}/match")
async def get_candidate_matches(job_id: int, db: AsyncSession = Depends(get_db)):
    return await match_candidates(job_id, db)
