from fastapi import APIRouter
from . import candidate, job  # Will create these next

router = APIRouter()

# Temporary empty routers for structure
router.include_router(candidate.router, prefix="/candidates", tags=["candidates"])
router.include_router(job.router, prefix="/jobs", tags=["jobs"])