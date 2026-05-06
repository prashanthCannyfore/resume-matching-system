from google import genai
from app.core.config import settings
import json
from typing import Dict

# Initialize client
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None


async def generate_candidate_insight(
    candidate: dict,
    job: dict,
    match_score: float,
    similarity: float,
    skill_score: float,
) -> Dict:

    if not client:
        return get_fallback_insight(candidate, job, match_score, similarity, skill_score)

    prompt = f"""
You are an expert senior technical recruiter and interviewer.

Analyze deeply and provide a highly specific candidate assessment for this job.

JOB:
Title: {job.get('title', 'N/A')}
Skills Required: {', '.join(job.get('required_skills', [])) or 'Not specified'}
Minimum Experience Required: {job.get('min_experience', 'Not specified')} years

CANDIDATE:
Name: {candidate.get('name', 'Candidate')}
Skills: {', '.join(candidate.get('skills', [])) or 'Not extracted'}
Experience: {candidate.get('experience_years', 0)} years

Match Score: {match_score:.3f}

STRICT RULES:
- Be SPECIFIC to this candidate and this job
- Mention EXACT matching skills by name
- Mention EXACT missing skills by name
- Refer to the required experience and whether the candidate meets it
- Explain why the score is this value using skills and experience
- Do not use generic phrases such as "strong candidate" or "good fit"
- Return valid JSON only, no extra text

Return JSON only:

{{
  "summary": "...specific evaluation...",
  "strengths": ["real matched skills or positive fit details"],
  "weaknesses": ["actual missing skills or weaker areas"],
  "skill_gaps": ["exact missing skills"],
  "match_explanation": "why score is X based on skills and experience"
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # ✅ fixed missing comma
            contents=prompt,
        )

        text = response.text.strip()

        # Handle markdown JSON (```json ... ```)
        if text.startswith("```"):
            text = text.split("```")[1].replace("json", "").strip()

        return json.loads(text)

    except Exception as e:
        print(f"Gemini error: {e}")
        return get_fallback_insight(candidate, job, match_score, similarity, skill_score)


def get_fallback_insight(candidate, job, match_score, similarity, skill_score):

    candidate_skills = set(candidate.get("skills", []))
    job_skills = set(job.get("required_skills", []))
    matched = sorted(candidate_skills & job_skills)
    missing = sorted(job_skills - candidate_skills)
    experience = candidate.get("experience_years", 0)
    min_experience = job.get("min_experience", 0)

    experience_message = (
        f"Candidate has {experience} years experience vs required {min_experience} years."
        if min_experience else
        f"Candidate has {experience} years experience."
    )

    if matched and missing:
        summary = (
            f"Candidate matches {len(matched)} of {len(job_skills)} required skills: {', '.join(matched)}. "
            f"Missing skills are: {', '.join(missing)}. {experience_message}"
        )
    elif matched:
        summary = (
            f"Candidate matches all required skills present in the profile: {', '.join(matched)}. "
            f"{experience_message}"
        )
    elif missing:
        summary = (
            f"Candidate does not match required skills for this role. Missing skills: {', '.join(missing)}. "
            f"{experience_message}"
        )
    else:
        summary = (
            f"No explicit required skills were extracted from the job or candidate profile. "
            f"{experience_message}"
        )

    strengths = [f"Matched skill: {skill}" for skill in matched[:3]] or ["No matched skills found"]
    weaknesses = [f"Missing skill: {skill}" for skill in missing[:3]] or ["No explicit missing skills detected"]
    skill_gaps = missing[:5]
    match_explanation = (
        f"The score is {match_score:.2f} because the candidate matched {len(matched)} required skill(s) and missed {len(missing)} required skill(s). "
        f"{experience_message}"
    )

    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "skill_gaps": skill_gaps,
        "match_explanation": match_explanation,
    }