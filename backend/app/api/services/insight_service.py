# app/api/services/insight_service.py
from groq import Groq
from app.core.config import settings
import json

client = Groq(api_key=settings.GROQ_API_KEY)

async def generate_candidate_insight(candidate: dict, job: dict, match_score: float, similarity: float, skill_score: float) -> dict:
    """
    Generate AI-powered insight using Groq (fast & cheap)
    """
    prompt = f"""
You are an expert technical recruiter.

**Job Position:**
Title: {job.get('title')}
Required Skills: {', '.join(job.get('required_skills', []))}
Minimum Experience: {job.get('min_experience', 0)} years

**Candidate Profile:**
Name: {candidate.get('name', 'Candidate')}
Skills: {', '.join(candidate.get('skills', []))}
Experience: {candidate.get('experience_years', 0)} years
Education: {candidate.get('education') or 'Not mentioned'}

**Match Data:**
Overall Match Score: {match_score:.3f}
Vector Similarity: {similarity:.3f}
Skill Match Score: {skill_score:.3f}

Generate a professional, concise recruiter insight in JSON format only with these exact keys:
{{
  "summary": "One sentence professional summary",
  "strengths": ["bullet point 1", "bullet point 2", "bullet point 3"],
  "weaknesses": ["bullet point 1", "bullet point 2"],
  "skill_gaps": ["skill gap 1", "skill gap 2"],
  "match_explanation": "Clear explanation why this candidate got this score"
}}
"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",   # or "mixtral-8x7b-32768"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600,
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
        # Fallback if Groq fails
        return {
            "summary": f"Strong match with score {match_score:.2f}",
            "strengths": ["Relevant skills found", "Good experience level"],
            "weaknesses": ["Some skill gaps possible"],
            "skill_gaps": ["Check missing skills manually"],
            "match_explanation": f"Hybrid score based on vector similarity ({similarity:.2f}) and skill match ({skill_score:.2f})"
        }