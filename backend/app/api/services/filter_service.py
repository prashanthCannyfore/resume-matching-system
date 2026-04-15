from typing import List, Dict


# -------------------------
# SKILL MATCH CHECK
# -------------------------
def has_skill_match(candidate_skills: List[str], job_skills: List[str], threshold: float = 0.3):
    if not job_skills:
        return True

    match_count = len(set(candidate_skills) & set(job_skills))
    return (match_count / len(job_skills)) >= threshold


# -------------------------
# EXPERIENCE CHECK
# -------------------------
def has_experience_match(candidate_exp: int, required_exp: int):
    return candidate_exp >= required_exp


# -------------------------
# NEW: SCORE CALCULATION 
# -------------------------
def calculate_score(candidate_skills: List[str], job_skills: List[str]):
    if not job_skills:
        return 0

    match_count = len(set(candidate_skills) & set(job_skills))
    return round(match_count / len(job_skills), 2)


# -------------------------
# MAIN FILTER FUNCTION
# -------------------------
def filter_candidates(candidates: List[Dict], job: Dict):
    filtered = []

    job_skills = job.get("required_skills", [])
    required_exp = job.get("min_experience", 0)

    for candidate in candidates:
        candidate_skills = candidate.get("skills", [])
        candidate_exp = candidate.get("experience_years", 0)

        # ✅ NEW: calculate score
        score = calculate_score(candidate_skills, job_skills)

        # ✅ UPDATED FILTER LOGIC
        if score >= 0.3 and has_experience_match(candidate_exp, required_exp):
            candidate["score"] = score   #  attach score
            filtered.append(candidate)

    # ✅ NEW: SORT BY BEST MATCH
    return sorted(filtered, key=lambda x: x["score"], reverse=True)