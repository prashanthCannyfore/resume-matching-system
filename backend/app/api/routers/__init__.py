from fastapi import APIRouter
from . import candidate, job, resume, match

router = APIRouter()

router.include_router(candidate.router, prefix="/candidates", tags=["candidates"])
router.include_router(job.router, prefix="/jobs", tags=["jobs"])
router.include_router(resume.router, prefix="/resume", tags=["resume"]) 
router.include_router(match.router, prefix="/match", tags=["matching"])