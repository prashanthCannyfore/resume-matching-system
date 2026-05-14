"""
Candidate insight generation.

CPU performance reality (llama3.2:3b, no GPU):
  ~0.3 tokens/sec → 150 output tokens ≈ 60-90s per call

Design decisions:
1. Prompt is kept under 400 tokens total (resume capped at 300 chars).
2. Output capped at 150 tokens — enough for a useful summary.
3. Each insight call has a hard 90s asyncio timeout.
4. On ANY failure (timeout, error, empty) → instant Python fallback.
5. All 5 insight calls run CONCURRENTLY (asyncio.gather) with a semaphore=1
   because Ollama on CPU can only handle one generate at a time anyway —
   but the gather structure means we don't block the event loop between calls.
6. Matching result is NEVER held back waiting for insights.
   Insights are generated after ranking is complete; if they all fail,
   fallback strings are used and the response still goes out.
"""
import asyncio
import logging
import time

import httpx

from app.api.services.ollama_client import generate
from app.api.services.parser import normalize_skill_list

logger = logging.getLogger(__name__)

# One Ollama generate at a time on CPU — parallel calls just queue up and
# each waits longer, making timeouts worse. Serialise them.
_INSIGHT_SEM = asyncio.Semaphore(1)

# Hard wall-clock timeout per insight call (asyncio level, not httpx level)
_INSIGHT_TIMEOUT_S = 90.0


async def generate_candidate_insight(
    candidate: dict,
    job: dict,
    match_score: float,
    similarity: float,
    skill_score: float,
) -> str:
    """
    Generate an AI insight for one candidate.
    ALWAYS returns a string — never raises, never blocks the caller.
    """
    name = candidate.get("name", "Candidate")
    t0   = time.monotonic()

    try:
        async with _INSIGHT_SEM:
            logger.info(f"[insight] Generating for {name!r} (timeout={_INSIGHT_TIMEOUT_S}s)")
            result = await asyncio.wait_for(
                _call_ollama(candidate, job, match_score),
                timeout=_INSIGHT_TIMEOUT_S,
            )
            elapsed = time.monotonic() - t0
            logger.info(f"[insight] Done for {name!r} in {elapsed:.1f}s")
            return result

    except asyncio.TimeoutError:
        elapsed = time.monotonic() - t0
        logger.warning(
            f"[insight] Timeout for {name!r} after {elapsed:.1f}s — using fallback"
        )
    except httpx.TimeoutException as e:
        logger.warning(f"[insight] HTTP timeout for {name!r}: {e} — using fallback")
    except Exception as e:
        logger.error(f"[insight] Error for {name!r}: {type(e).__name__}: {e} — using fallback")

    return _fallback_insight(candidate, job, match_score, similarity, skill_score)


async def _call_ollama(candidate: dict, job: dict, match_score: float) -> str:
    """Build a minimal prompt and call Ollama generate."""
    prompt = _build_compact_prompt(candidate, job, match_score)
    response = await generate(
        prompt=prompt,
        temperature=0.1,
        max_tokens=150,     # ~45s on CPU at 0.3 tok/s
    )
    if response and response.strip():
        return response.strip()
    # Empty response → use fallback
    raise ValueError("Empty response from Ollama")


def _build_compact_prompt(candidate: dict, job: dict, match_score: float) -> str:
    """
    Compact prompt — total ~300-400 tokens.
    Previous prompt was ~2000 tokens which caused timeouts.
    """
    candidate_exp   = candidate.get("experience_years", 0)
    matched_skills  = candidate.get("matched_skills", [])
    missing_skills  = candidate.get("missing_skills", [])
    min_exp         = job.get("min_experience", 0)
    job_skills      = job.get("required_skills", [])

    # Cap resume to 300 chars — enough context, avoids token explosion
    resume_ctx = (candidate.get("resume_text") or "")[:300].replace("\n", " ")

    verdict = (
        "Strong Fit" if candidate_exp >= min_exp
        else "Good Fit" if min_exp == 0 or candidate_exp >= min_exp * 0.8
        else "Underqualified"
    )

    matched_str = ", ".join(matched_skills) if matched_skills else "None"
    missing_str = ", ".join(missing_skills) if missing_skills else "None"

    return (
        f"Recruiter insight for candidate applying to role requiring: {', '.join(job_skills)}.\n"
        f"Experience: {candidate_exp} yrs (required: {min_exp} yrs). "
        f"Match score: {match_score:.0%}. "
        f"Matched skills: {matched_str}. "
        f"Missing skills: {missing_str}. "
        f"Verdict: {verdict}.\n"
        f"Resume context: {resume_ctx}\n\n"
        f"Write a 3-sentence professional recruiter summary covering fit, strengths, and recommendation."
    )


# ── Pure-Python fallback — instant, no LLM needed ────────────────────────────
def _fallback_insight(
    candidate: dict,
    job: dict,
    match_score: float,
    similarity: float,
    skill_score: float,
) -> str:
    job_skills     = set(normalize_skill_list(job.get("required_skills", [])))
    experience     = candidate.get("experience_years", 0)
    min_experience = job.get("min_experience", 0)

    matched = candidate.get("matched_skills") or sorted(
        set(normalize_skill_list(candidate.get("skills", []))) & job_skills
    )
    missing = candidate.get("missing_skills") or sorted(
        job_skills - set(normalize_skill_list(candidate.get("skills", [])))
    )
    total_required = len(job_skills)

    verdict = (
        "Strong Fit"    if experience >= min_experience
        else "Good Fit" if min_experience == 0 or experience >= min_experience * 0.8
        else "Underqualified"
    )

    recommendation = (
        "Hire"      if len(matched) == total_required and experience >= min_experience
        else "Consider" if matched and experience >= min_experience * 0.75
        else "Reject"
    )

    matched_list = "\n- ".join(matched) if matched else "None"
    missing_list = "\n- ".join(missing) if missing else "None"

    return f"""📊 Match Summary
- Match Score: {match_score:.1%}
- Skill Match: {len(matched)}/{total_required}
- Experience: {experience} years

---

✅ Matched Skills:
- {matched_list}

❌ Missing Skills:
- {missing_list}

---

📈 Experience Analysis:
- Candidate Experience: {experience} years
- Required Experience: {min_experience} years
- Verdict: {verdict}

---

🤖 AI Recruiter Insight:
Candidate has {experience} years of experience with {len(matched)}/{total_required} required skills matched ({matched_list}). {"Experience requirement met." if experience >= min_experience else f"Experience gap of {min_experience - experience:.1f} years."} {"All required skills present — strong technical fit." if not missing else f"Missing: {missing_list}."}

---

💬 Final Recommendation:
- {recommendation}
- Reason: Skill match {len(matched)}/{total_required}, experience {experience} yrs (required {min_experience} yrs)."""
