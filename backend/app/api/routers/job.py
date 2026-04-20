from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.services.job_service import process_job_description, create_job
from app.api.schemas.job import JobCreate

router = APIRouter()


@router.post("/")
async def create_job_api(
    job: JobCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    description = job.description_text or ""
    title = job.title or "Job Role"

    # ✅ fallback to raw text
    if not description:
        try:
            raw_text = (await request.body()).decode("utf-8")
            description = raw_text
        except Exception:
            pass

    # dynamic object
    class JobData:
        pass

    job_data = JobData()
    job_data.title = title
    job_data.description_text = description
    job_data.company = job.company
    job_data.location = job.location

    return await create_job(job_data, db)


@router.post("/upload")
async def upload_job(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    return await process_job_description(file, db)
