from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.models.candidate import Candidate
from app.api.models.job import JobDescription

from app.api.services.embedding_service import generate_embedding
from app.api.services.vector_store import search_similar
from app.api.services.filter_service import filter_and_rank_candidates


TOP_N_RESULTS = 5  # final number of candidates to return


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
        {"id": c.id, "skills": c.skills, "experience_years": c.experience_years}
        for c in candidates
    ]

    # -------------------------
    # GENERATE JOB EMBEDDING
    # -------------------------
    if not job.description_text:
        return {"error": "Job description is empty"}

    job_embedding = generate_embedding(job.description_text)

    if not job_embedding:
        return {"error": "Failed to generate embedding"}

    # -------------------------
    # VECTOR SEARCH
    # -------------------------
    similarity_results = search_similar(job_embedding, top_k=5)

    if not similarity_results:
        return {"job_id": job_id, "matches": []}

    # -------------------------
    # HYBRID FILTER + RANK
    # -------------------------
    ranked_candidates = filter_and_rank_candidates(
        candidate_list,
        {"required_skills": job.required_skills, "min_experience": job.min_experience},
        similarity_results,
    )

    # -------------------------
    # RETURN TOP N
    # -------------------------
    return {"job_id": job_id, "matches": ranked_candidates[:TOP_N_RESULTS]}
