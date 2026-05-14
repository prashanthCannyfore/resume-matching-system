"""
Candidate insight generation — backed by local Ollama LLM.
Forces exact structured format.
"""
import asyncio
import logging
import time

from app.api.services.ollama_client import generate
from app.api.services.parser import normalize_skill_list

logger = logging.getLogger(__name__)

_INSIGHT_SEM = asyncio.Semaphore(1)
_INSIGHT_TIMEOUT_S = 90.0


async def generate_candidate_insight(
    candidate: dict,
    job: dict,
    match_score: float,
    similarity: float,
    skill_score: float,
) -> str:
    name = candidate.get("name", "Candidate")
    t0 = time.monotonic()

    try:
        async with _INSIGHT_SEM:
            result = await asyncio.wait_for(
                _call_ollama(candidate, job, match_score, similarity, skill_score),
                timeout=_INSIGHT_TIMEOUT_S,
            )
            elapsed = time.monotonic() - t0
            logger.info(f"[insight] Done for {name!r} in {elapsed:.1f}s")
            return result

    except Exception as e:
        logger.error(f"[insight] Failed for {name!r}: {e}")
        return _fallback_insight(candidate, job, match_score, similarity, skill_score)


async def _call_ollama(candidate: dict, job: dict, match_score: float, similarity: float, skill_score: float) -> str:
    prompt = _build_structured_prompt(candidate, job, match_score, similarity, skill_score)
    
    response = await generate(
        prompt=prompt,
        temperature=0.1,
        max_tokens=800,
    )
    
    if response and any(marker in response for marker in ["📊 Match Summary", "✅ Matched Skills"]):
        return response.strip()
    
    logger.warning("Ollama did not return structured format, using fallback")
    return _fallback_insight(candidate, job, match_score, similarity, skill_score)


def _build_structured_prompt(candidate: dict, job: dict, match_score: float, similarity: float, skill_score: float) -> str:
    required_skills = ", ".join(job.get("required_skills", []))
    min_exp = job.get("min_experience", 0)
    resume_snippet = (candidate.get("resume_text") or "")[:1400]

    matched_skills = candidate.get("matched_skills", [])
    missing_skills = candidate.get("missing_skills", [])

    return f"""You are a senior AI recruiter. Analyse the candidate strictly using the given data.

**STRICT OUTPUT RULES**:
- Use EXACTLY the format below.
- Do NOT add any extra text before or after.
- Do NOT change section titles or emojis.

📊 Match Summary
- Match Score: {match_score:.1%}
- Skill Match: {len(matched_skills)}/{len(job.get("required_skills", []))}
- Experience: {candidate.get("experience_years", 0)} years

---

✅ Matched Skills:
- {", ".join(matched_skills) if matched_skills else "None"}

❌ Missing Skills:
- {", ".join(missing_skills) if missing_skills else "None"}

---

📈 Experience Analysis:
- Candidate Experience: {candidate.get("experience_years", 0)} years
- Required Experience: {min_exp} years
- Verdict: {"Strong Fit" if candidate.get("experience_years", 0) >= min_exp else "Good Fit" if min_exp == 0 or candidate.get("experience_years", 0) >= min_exp * 0.8 else "Underqualified"}

---

🎯 Role Fit Analysis:
- Relevant Experience: <based on resume>
- Transferable Skills: <list key skills>
- Domain Fit: <tech / design / etc>

---

🧠 Strengths:
- <3-5 bullet points>

---

⚠️ Gaps / Risks:
- <list gaps or "No major gaps">

---

🤖 AI Recruiter Insight (DETAILED):
<4-6 lines professional evaluation>

---

💬 Final Recommendation:
- <Hire / Consider / Reject>
- Reason: <short justification>

---

JOB: {job.get("title", "React Developer")} requiring {required_skills}
EXPERIENCE REQUIRED: {min_exp} years

RESUME:
{resume_snippet}
"""