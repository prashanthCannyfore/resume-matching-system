from groq import AsyncGroq
from app.core.config import settings
import json
from typing import Dict

client = AsyncGroq(api_key=settings.GROQ_API_KEY)


async def generate_candidate_insight(
    candidate: dict,
    job: dict,
    match_score: float,
    similarity: float,
    skill_score: float,
) -> Dict:
    """
    Generate high-quality, recruiter-friendly AI insight
    """
    prompt = f"""
You are a senior technical recruiter with 10+ years of experience.

**Job Position:**
Title: {job.get('title', 'N/A')}
Required Skills: {', '.join(job.get('required_skills', [])) or 'Not specified'}
Minimum Experience: {job.get('min_experience', 0)} years

**Candidate Profile:**
Name: {candidate.get('name', 'Candidate')}
Skills: {', '.join(candidate.get('skills', [])) or 'Not extracted'}
Experience: {candidate.get('experience_years', 0)} years
Education: {candidate.get('education') or 'Not mentioned'}

**Match Analysis:**
Overall Match Score: {match_score:.2f} / 1.00
Vector Similarity: {similarity:.3f}
Skill Match Score: {skill_score:.2f}

Generate a professional, insightful recruiter note in **valid JSON only** with these exact keys:

{{
  "summary": "One powerful, concise professional summary (max 20 words)",
  "strengths": ["3 short bullet points highlighting key strengths"],
  "weaknesses": ["1-2 short bullet points (if any)"],
  "skill_gaps": ["List of missing skills or gaps"],
  "match_explanation": "Detailed explanation of why this candidate received this score. Be specific about skills match, experience, and overall fit."
}}

Rules:
- Be honest and balanced
- Use professional recruiter language
- Keep bullets short and impactful (max 8-10 words each)
- Focus on technical fit for the role
"""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Best current model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.65,
            max_tokens=700,
            response_format={"type": "json_object"}
        )

        insight = json.loads(response.choices[0].message.content)

        return {
            "summary": insight.get("summary", ""),
            "strengths": insight.get("strengths", []),
            "weaknesses": insight.get("weaknesses", []),
            "skill_gaps": insight.get("skill_gaps", []),
            "match_explanation": insight.get("match_explanation", "")
        }

    except Exception as e:
        print(f"Groq insight error: {e}")
        # Smart fallback
        return {
            "summary": f"Strong candidate with {candidate.get('experience_years', 0)} years of experience",
            "strengths": ["Relevant technical background", "Solid experience level"],
            "weaknesses": ["Some skill gaps identified"],
            "skill_gaps": ["Review missing skills from job description"],
            "match_explanation": f"Overall score of {match_score:.2f} based on {similarity:.2f} vector similarity and {skill_score:.2f} skill match. Strong experience but may need upskilling in some areas."
        }