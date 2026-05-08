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


async def match_candidates(job_id: int, db: AsyncSession, sort_by: str = "score"):
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
            "skills": c.skills or [],
            "experience_years": c.experience_years or 0,
            "education": c.education,
            "resume_text": (c.resume_text or "")[:800],
        }
        for c in candidates
    ]

    # ------------------------- EMBEDDING -------------------------
    job_embedding = generate_embedding(job.description_text)

    if not job_embedding:
        return {"error": "Failed to generate embedding"}

    # ------------------------- VECTOR SEARCH -------------------------
    similarity_results = search_similar(job_embedding, top_k=10)

    if not similarity_results:
        return {
            "job_id": job_id,
            "job_title": job.title,
            "error": "No candidates found in vector store. Please upload resumes first.",
            "matches": [],
        }

    # ------------------------- HYBRID FILTER + RANK -------------------------
    ranked_candidates = filter_and_rank_candidates(
        candidate_list,
        {
            "required_skills": job.required_skills,
            "min_experience": job.min_experience,
        },
        similarity_results,
    )

    # ------------------------- FINAL SCORE CALCULATION -------------------------
    for cand in ranked_candidates:
        similarity = cand.get("similarity", 0)
        skill_score = cand.get("skill_score", 0)
        candidate_exp = cand.get("experience_years", 0)
        required_exp = job.min_experience or 0

        experience_match = (
            1.0 if required_exp == 0
            else (1.0 if candidate_exp >= required_exp else candidate_exp / required_exp)
        )

        # Perfect match: all skills present + experience met → 100%
        if skill_score >= 1.0 and experience_match >= 1.0:
            cand["final_score"] = 1.0
        else:
            cand["final_score"] = round(
                0.5 * similarity + 0.3 * skill_score + 0.2 * experience_match, 3
            )

    # ------------------------- SORTING -------------------------
    if sort_by == "experience":
        ranked_candidates.sort(
            key=lambda x: x.get("experience_years", 0),
            reverse=True
        )

    elif sort_by == "similarity":
        ranked_candidates.sort(
            key=lambda x: x.get("similarity", 0),
            reverse=True
        )

    else:  # default = score
        ranked_candidates.sort(
            key=lambda x: x.get("final_score", 0),
            reverse=True
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
            match_score=cand.get("final_score", 0),
            similarity=cand.get("similarity", 0),
            skill_score=cand.get("skill_score", 0),
        )

        final_matches.append({**cand, "insight": insight})

    return {
        "job_id": job_id,
        "job_title": job.title,
        "total_candidates": len(candidate_list),
        "sort_by": sort_by,
        "matches": final_matches,
    }