from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.models.candidate import Candidate
import os

router = APIRouter()


@router.get("/")
async def get_candidates(db: AsyncSession = Depends(get_db)):
    return {"message": "Candidates endpoint - coming soon"}


@router.get("/{candidate_id}/download")
async def download_resume(candidate_id: int, db: AsyncSession = Depends(get_db)):
    # Get candidate from database
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Construct file path
    file_path = os.path.join("uploads", candidate.name)

    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Resume file not found")

    # Return file as download
    return FileResponse(
        path=file_path,
        filename=candidate.name,
        media_type='application/octet-stream'
    )
