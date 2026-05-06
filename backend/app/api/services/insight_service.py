from google import genai
from app.core.config import settings
from app.api.services.parser import normalize_skill_list
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
You are a senior AI recruiter and talent evaluation expert.

Your task is to analyze the resume against the job description and generate a detailed candidate match report.

---

STRICT RULES:
- If total experience is explicitly mentioned (e.g., 6.5 years), use it EXACTLY (do NOT round to 6)
- Do NOT modify numeric values
- Extract skills ONLY from the SKILLS section
- Normalize skills (e.g., "XD" = "Adobe XD", case-insensitive)
- If a skill is present, it MUST be counted as matched
- Do NOT hallucinate missing skills
- Base all insights ONLY on given data

---

MATCHING LOGIC:
- Skill Match = matched_required_skills / total_required_skills
- Experience Match:
  - If candidate experience >= required → 1
  - Else → (candidate / required)

Final Score:
Score = (0.7 × Skill Match) + (0.3 × Experience Match)

---

OUTPUT FORMAT:

📊 Match Summary
- Match Score: <percentage>
- Skill Match: <x/y>
- Experience: <exact years from resume>

---

✅ Matched Skills:
- <list>

❌ Missing Skills:
- <list or "None">

---

📈 Experience Analysis:
- Candidate Experience: <exact years>
- Required Experience: <years>
- Verdict: <Strong Fit / Good Fit / Underqualified>
- Insight: <short reasoning>

---

🎯 Role Fit Analysis:
- Relevant Experience:
  <specific work aligned to JD>
- Transferable Skills:
  <related capabilities>
- Domain Fit:
  <industries worked in>

---

📊 Impact Highlights:
- <quantified achievements>
- <campaigns / users / brands>
- <leadership or mentoring>

---

🧠 Strengths:
- <3–5 strong points backed by resume>

---

⚠️ Gaps / Risks:
- <missing areas or unclear signals>
- <example: no backend, limited domain depth, etc.>

---

🤖 AI Recruiter Insight (DETAILED):
Write a 4–6 line recruiter-style evaluation covering:
- Overall fit for the role
- Why the candidate is suitable or not
- Strength in required skills (explicit mention)
- Experience relevance (DO NOT round values)
- Any hiring risk or limitation

---

💬 Final Recommendation:
- Hire / Consider / Reject
- Reason: <clear justification>

---

INPUT:

JOB DESCRIPTION:
Required Skills: {', '.join(job.get('required_skills', []))}
Required Experience: {job.get('min_experience', 0)} years

RESUME:
{candidate.get('resume_text', '')}
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

        return text

    except Exception as e:
        print(f"Gemini error: {e}")
        return get_fallback_insight(candidate, job, match_score, similarity, skill_score)


def get_fallback_insight(candidate, job, match_score, similarity, skill_score):

    candidate_skills = set(normalize_skill_list(candidate.get("skills", [])))
    job_skills = set(normalize_skill_list(job.get("required_skills", [])))
    matched = sorted(candidate_skills & job_skills)
    missing = sorted(job_skills - candidate_skills)
    experience = candidate.get("experience_years", 0)
    min_experience = job.get("min_experience", 0)

    skill_match_ratio = len(matched) / len(job_skills) if job_skills else 0
    experience_match = 1 if experience >= min_experience else (experience / min_experience) if min_experience > 0 else 0
    calculated_score = 0.7 * skill_match_ratio + 0.3 * experience_match

    verdict = "Strong Fit" if experience >= min_experience else "Good Fit" if experience >= min_experience * 0.8 else "Underqualified"

    matched_list = "\n- ".join(matched) if matched else "None"
    missing_list = "\n- ".join(missing) if missing else "None"

def get_fallback_insight(candidate, job, match_score, similarity, skill_score):

    candidate_skills = set(normalize_skill_list(candidate.get("skills", [])))
    job_skills = set(normalize_skill_list(job.get("required_skills", [])))
    matched = sorted(candidate_skills & job_skills)
    missing = sorted(job_skills - candidate_skills)
    experience = candidate.get("experience_years", 0)
    min_experience = job.get("min_experience", 0)
    resume_text = candidate.get("resume_text", "").lower()

    skill_match_ratio = len(matched) / len(job_skills) if job_skills else 0
    experience_match = 1 if experience >= min_experience else (experience / min_experience) if min_experience > 0 else 0

    verdict = "Strong Fit" if experience >= min_experience else "Good Fit" if experience >= min_experience * 0.8 else "Underqualified"

    matched_list = "\n- ".join(matched) if matched else "None"
    missing_list = "\n- ".join(missing) if missing else "None"

    # Dynamically extract from resume text
    has_leadership = "led" in resume_text or "mentored" in resume_text or "manager" in resume_text or "head" in resume_text
    has_campaigns = "campaign" in resume_text or "project" in resume_text
    has_brands = "brand" in resume_text or "brands" in resume_text
    has_teams = "team" in resume_text or "collaborated" in resume_text or "worked with" in resume_text

    # Extract industries
    industries_found = []
    if "fmcg" in resume_text:
        industries_found.append("FMCG")
    if "tech" in resume_text or "software" in resume_text or "data" in resume_text or "machine learning" in resume_text:
        industries_found.append("Tech/Software")
    if "hospitality" in resume_text or "hotel" in resume_text or "restaurant" in resume_text:
        industries_found.append("Hospitality")
    if "finance" in resume_text or "banking" in resume_text or "investment" in resume_text:
        industries_found.append("Finance")
    if "healthcare" in resume_text or "medical" in resume_text or "pharma" in resume_text:
        industries_found.append("Healthcare")
    if "retail" in resume_text or "ecommerce" in resume_text:
        industries_found.append("Retail/E-commerce")

    domain_fit = ", ".join(industries_found) if industries_found else "General"

    # Build role fit dynamically
    role_fit_list = []
    if has_campaigns:
        role_fit_list.append("Project and campaign execution")
    if has_teams:
        role_fit_list.append("Team collaboration and coordination")
    if has_leadership:
        role_fit_list.append("Leadership and team management")
    if "analysis" in resume_text or "analytics" in resume_text:
        role_fit_list.append("Data analysis and insights")
    if "research" in resume_text:
        role_fit_list.append("Research experience")

    relevant_exp = "; ".join(role_fit_list) if role_fit_list else "Professional experience in related field"

    # Build impact highlights dynamically
    impact_lines = []
    import re
    numbers = re.findall(r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|months?|projects?|clients?|users?|brands?|impressions?|ratings?|campaigns?)", resume_text, re.I)
    if numbers:
        impact_lines.append(f"Quantified impact in profile")
    if has_leadership:
        impact_lines.append("Leadership and team management experience")
    if has_brands:
        impact_lines.append(f"Work with multiple brands and clients")

    impact_text = "\n- ".join(impact_lines) if impact_lines else "Professional experience"

    # Strengths based on skills and role
    strengths_list = []
    if matched:
        strengths_list.append(f"Proficiency in: {', '.join(matched[:2])}")
    if has_campaigns or "project" in resume_text:
        strengths_list.append("Project execution and delivery")
    if has_leadership:
        strengths_list.append("Leadership capabilities")
    if len(candidate_skills) > 2:
        strengths_list.append(f"Diverse skill set ({len(candidate_skills)} skills)")

    strengths_text = "\n- ".join(strengths_list) if strengths_list else "Professional background in field"

    # Gaps/risks based on missing skills
    gaps_list = []
    if missing:
        gaps_list.append(f"Missing required skills: {', '.join(missing)}")
    if experience < min_experience and min_experience > 0:
        gaps_list.append(f"Experience gap: {min_experience - experience:.1f} years below requirement")
    if len(candidate_skills) < len(job_skills) and len(job_skills) > 1:
        gaps_list.append("Limited skill coverage for full role scope")
    if not has_leadership and "senior" in job.get("title", "").lower():
        gaps_list.append("No clear leadership background for senior role")

    gaps_text = "\n- ".join(gaps_list) if gaps_list else "No significant gaps identified"

    # Build AI insight based on actual data
    if matched and experience >= min_experience:
        ai_insight = f"Strong fit. Candidate has {experience} years experience and all required skills: {', '.join(matched)}. Proven track record in {domain_fit}."
    elif matched and experience < min_experience:
        ai_insight = f"Technical match on skills ({', '.join(matched)}), but experience is {experience} years vs {min_experience} required. Consider if trainable on experience."
    elif not matched and experience >= min_experience:
        ai_insight = f"Experienced candidate ({experience} years) but lacks critical skills ({', '.join(missing)}). Would need training on {', '.join(missing[:2])}."
    else:
        ai_insight = f"Weak fit. Missing required skills ({', '.join(missing)}) and experience ({experience}/{min_experience} years). Not recommended."

    recommendation = "Hire" if len(matched) == len(job_skills) and experience >= min_experience else "Consider" if len(matched) > 0 and experience >= min_experience * 0.75 else "Reject"
    reason = f"Skill match: {len(matched)}/{len(job_skills)}. Experience: {experience} years (required: {min_experience})."

    return f"""
📊 Match Summary
- Match Score: {match_score:.1%}
- Skill Match: {len(matched)}/{len(job_skills)}
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
- Insight: {'Meets experience requirements.' if experience >= min_experience else f'{min_experience - experience:.1f} years below requirement.'}

---

🎯 Role Fit Analysis:
- Relevant Experience:
  {relevant_exp}
- Transferable Skills:
  {', '.join(list(candidate_skills)[:3]) if candidate_skills else 'To be evaluated'}
- Domain Fit:
  {domain_fit}

---

📊 Impact Highlights:
- {impact_text}

---

🧠 Strengths:
- {strengths_text}

---

⚠️ Gaps / Risks:
- {gaps_text}

---

🤖 AI Recruiter Insight (DETAILED):
{ai_insight}

---

💬 Final Recommendation:
- {recommendation}
- Reason: {reason}
""".strip()