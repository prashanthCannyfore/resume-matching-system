from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.models.candidate import Candidate
from app.api.models.job import JobDescription

from app.api.services.embedding_service import generate_embedding
from app.api.services.vector_store import search_similar
from app.api.services.filter_service import filter_and_rank_candidates


async def match_candidates(job_id: int, db: AsyncSession):
    # -------------------------
    # GET JOB
    # -------------------------
    job = await db.get(JobDescription, job_id)

    if not job:
        return {"error": "Job not found"}

    # -------------------------
    # GET ALL CANDIDATES
    # -------------------------
    result = await db.execute(select(Candidate))
    candidates = result.scalars().all()

    candidate_list = [
        {
            "id": c.id,
            "skills": c.skills,
            "experience_years": c.experience_years
        }
        for c in candidates
    ]

    # -------------------------
    # VECTOR SEARCH
    # -------------------------
    job_embedding = generate_embedding(job.description_text)

    similarity_results = search_similar(job_embedding, top_k=10)

    # -------------------------
    # HYBRID FILTER + RANK
    # -------------------------
    ranked = filter_and_rank_candidates(
        candidate_list,
        {
            "required_skills": job.required_skills,
            "min_experience": job.min_experience
        },
        similarity_results
    )

    return {
        "job_id": job_id,
        "matches": ranked
    }