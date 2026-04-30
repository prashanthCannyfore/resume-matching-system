from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.models.candidate import Candidate
from app.api.models.job import JobDescription

from app.api.services.embedding_service import generate_embedding
from app.api.services.vector_store import search_similar
from app.api.services.filter_service import filter_and_rank_candidates
from app.api.services.insight_service import generate_candidate_insight
from app.api.services.parser import extract_skills

TOP_N_RESULTS = 5


async def match_candidates(job_id: int, db: AsyncSession):
    job = await db.get(JobDescription, job_id)
    if not job:
        return {"error": "Job not found"}

    # ------------------------- AUTO-FIX EMPTY SKILLS -------------------------
    if not job.required_skills:
        print(f"Job {job_id} had empty skills → re-extracting now")
        job.required_skills = await extract_skills(job.description_text, db)
        await db.commit()

    # ------------------------- GET CANDIDATES -------------------------
    result = await db.execute(select(Candidate))
    candidates = result.scalars().all()

    candidate_list = [
        {
            "id": c.id,
            "name": c.name,
            "skills": c.skills,
            "experience_years": c.experience_years,
            "education": c.education,
            "resume_text": c.resume_text[:800],
        }
        for c in candidates
    ]

    # ------------------------- VECTOR SEARCH -------------------------
    job_embedding = generate_embedding(job.description_text)

    if not job_embedding:
        return {"error": "Failed to generate embedding"}

    # -------------------------
    # VECTOR SEARCH
    # -------------------------
    similarity_results = search_similar(job_embedding, top_k=5)

    if not similarity_results:
        return {
            "job_id": job_id,
            "job_title": job.title,
            "error": "No candidates found in vector store. Please upload some resumes first.",
            "matches": [],
        }

    # ------------------------- HYBRID FILTER + RANK -------------------------
    ranked_candidates = filter_and_rank_candidates(
        candidate_list,
        {"required_skills": job.required_skills, "min_experience": job.min_experience},
        similarity_results,
    )

    # ------------------------- AI INSIGHTS -------------------------
    final_matches = []
    for cand in ranked_candidates[:TOP_N_RESULTS]:
        insight = await generate_candidate_insight(
            candidate=cand,
            job={
                "title": job.title,
                "required_skills": job.required_skills,
                "min_experience": job.min_experience,
            },
            match_score=cand["score"],
            similarity=cand["similarity"],
            skill_score=cand.get("skill_score", 0),
        )

        final_matches.append({**cand, "insight": insight})

    return {
        "job_id": job_id,
        "job_title": job.title,
        "total_candidates": len(candidate_list),
        "matches": final_matches,
    }
