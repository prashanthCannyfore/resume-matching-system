"""
Candidate matching service.

Insight generation is run concurrently for all top-N candidates using
asyncio.gather. Each insight call has its own timeout + fallback inside
insight_service, so a slow/failing Ollama never blocks the response.

Response contract is frozen — do NOT rename any key.
Frontend reads: job_id, job_title, required_skills, total_candidates,
                sort_by, matches[]
Each match:     id, name, email, skills, experience_years, education,
                final_score, similarity, skill_score,
                matched_skills, missing_skills, insight
"""
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.models.candidate import Candidate
from app.api.models.job import JobDescription

from app.api.services.embedding_service import generate_embedding_async as generate_embedding
from app.api.services.vector_store import search_similar
from app.api.services.filter_service import filter_and_rank_candidates
from app.api.services.insight_service import generate_candidate_insight
from app.api.services.parser import extract_skills

logger = logging.getLogger(__name__)
TOP_N_RESULTS = 5


async def match_candidates(job_id: int, db: AsyncSession, sort_by: str = "score"):
    # ── 1. Load job ───────────────────────────────────────────────────────────
    job = await db.get(JobDescription, job_id)
    if not job:
        return {"error": "Job not found"}

    if not job.required_skills:
        logger.info(f"[match] Job {job_id} had empty skills — re-extracting")
        job.required_skills = await extract_skills(job.description_text, db)
        await db.commit()

    # ── 2. Load candidates ────────────────────────────────────────────────────
    result     = await db.execute(select(Candidate))
    candidates = result.scalars().all()

    candidate_list = [
        {
            "id":               c.id,
            "name":             c.name,
            "email":            c.email,
            "skills":           c.skills or [],
            "experience_years": c.experience_years or 0,
            "education":        c.education,
            "resume_text":      c.resume_text or "",
        }
        for c in candidates
    ]

    logger.info(
        f"[match] Job {job_id} | skills={job.required_skills} | "
        f"candidates_in_db={len(candidate_list)}"
    )

    # ── 3. Embed job description ──────────────────────────────────────────────
    job_embedding = await generate_embedding(job.description_text)

    if not job_embedding or all(v == 0.0 for v in job_embedding[:10]):
        logger.error(f"[match] Job {job_id}: zero embedding — is Ollama running?")
        return {
            "job_id":           job_id,
            "job_title":        job.title,
            "required_skills":  job.required_skills,
            "total_candidates": len(candidate_list),
            "sort_by":          sort_by,
            "error":            "Embedding failed. Run: ollama serve",
            "matches":          [],
        }

    logger.info(f"[match] Job embedding dim={len(job_embedding)}")

    # ── 4. FAISS similarity search ────────────────────────────────────────────
    similarity_results = search_similar(job_embedding, top_k=len(candidate_list) or 10)
    logger.info(f"[match] FAISS returned {len(similarity_results)} results")

    if not similarity_results:
        return {
            "job_id":           job_id,
            "job_title":        job.title,
            "required_skills":  job.required_skills,
            "total_candidates": len(candidate_list),
            "sort_by":          sort_by,
            "error":            "No candidates in vector store. Upload resumes first.",
            "matches":          [],
        }

    # ── 5. Hybrid filter + rank ───────────────────────────────────────────────
    ranked_candidates = filter_and_rank_candidates(
        candidate_list,
        {"required_skills": job.required_skills, "min_experience": job.min_experience},
        similarity_results,
    )
    logger.info(f"[match] After filter+rank: {len(ranked_candidates)} candidates")

    # ── 6. Final score (same weights as filter_service for consistency) ──────
    required_exp = job.min_experience or 0
    has_required_skills = bool(job.required_skills)

    for cand in ranked_candidates:
        similarity    = cand.get("similarity", 0)
        skill_score   = cand.get("skill_score", 0)
        candidate_exp = cand.get("experience_years", 0)

        if required_exp == 0:
            exp_match = 1.0
        elif candidate_exp >= required_exp:
            exp_match = 1.0
        else:
            exp_match = round(candidate_exp / required_exp, 3)

        # Perfect match shortcut
        if skill_score >= 1.0 and exp_match >= 1.0:
            final = 1.0
        else:
            final = round(
                0.70 * skill_score
                + 0.20 * similarity
                + 0.10 * exp_match,
                3,
            )
            # Hard cap for zero-skill-match candidates
            if has_required_skills and skill_score == 0.0:
                final = min(final, 0.30)

        cand["final_score"] = final

        logger.debug(
            f"[match] {cand['name']!r} | "
            f"skill={skill_score:.3f} sim={similarity:.3f} "
            f"exp={exp_match:.3f} final={final:.3f}"
        )

    # ── 7. Sort ───────────────────────────────────────────────────────────────
    if sort_by == "experience":
        ranked_candidates.sort(key=lambda x: x.get("experience_years", 0), reverse=True)
    elif sort_by == "similarity":
        ranked_candidates.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    else:
        ranked_candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    top_candidates = ranked_candidates[:TOP_N_RESULTS]

    # ── 8. Generate insights CONCURRENTLY ────────────────────────────────────
    # Each call has its own timeout + fallback inside generate_candidate_insight.
    # asyncio.gather ensures we don't block the event loop between calls.
    # return_exceptions=True means one failure never cancels the others.
    logger.info(f"[match] Generating insights for {len(top_candidates)} candidates")

    job_ctx = {
        "title":          job.title,
        "required_skills": job.required_skills,
        "min_experience": job.min_experience,
    }

    insight_tasks = [
        generate_candidate_insight(
            candidate=cand,
            job=job_ctx,
            match_score=cand.get("final_score", 0),
            similarity=cand.get("similarity", 0),
            skill_score=cand.get("skill_score", 0),
        )
        for cand in top_candidates
    ]

    # return_exceptions=True — if one insight crashes, others still complete
    insights = await asyncio.gather(*insight_tasks, return_exceptions=True)

    # ── 9. Build response — frozen contract ───────────────────────────────────
    final_matches = []
    for cand, insight in zip(top_candidates, insights):
        # If gather returned an exception object, use fallback text
        if isinstance(insight, Exception):
            logger.error(f"[match] Insight gather exception for {cand['name']}: {insight}")
            from app.api.services.insight_service import _fallback_insight
            insight_text = _fallback_insight(
                cand, job_ctx,
                cand.get("final_score", 0),
                cand.get("similarity", 0),
                cand.get("skill_score", 0),
            )
        else:
            insight_text = insight

        final_matches.append({
            "id":               cand["id"],
            "name":             cand["name"],
            "email":            cand.get("email"),
            "skills":           cand.get("skills", []),
            "experience_years": cand.get("experience_years", 0),
            "education":        cand.get("education"),
            "final_score":      cand.get("final_score", 0),
            "similarity":       cand.get("similarity", 0),
            "skill_score":      cand.get("skill_score", 0),
            "matched_skills":   cand.get("matched_skills", []),
            "missing_skills":   cand.get("missing_skills", []),
            "insight":          insight_text,
        })

    logger.info(
        f"[match] Returning {len(final_matches)} matches | "
        f"scores={[m['final_score'] for m in final_matches]}"
    )

    return {
        "job_id":           job_id,
        "job_title":        job.title,
        "required_skills":  job.required_skills,
        "total_candidates": len(candidate_list),
        "sort_by":          sort_by,
        "matches":          final_matches,
    }
