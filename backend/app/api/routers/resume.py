from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.services.resume_service import process_resume

router = APIRouter()


@router.post("/upload")
async def upload_resume(file: UploadFile, db: AsyncSession = Depends(get_db)):
    return await process_resume(file, db)
