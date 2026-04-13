from typing import List, Dict


def has_skill_match(candidate_skills: List[str], job_skills: List[str], threshold: float = 0.3):
    """
    Returns True if candidate meets minimum skill overlap
    """
    if not job_skills:
        return True

    match_count = len(set(candidate_skills) & set(job_skills))
    return (match_count / len(job_skills)) >= threshold


def has_experience_match(candidate_exp: int, required_exp: int):
    """
    Candidate must meet minimum experience requirement
    """
    return candidate_exp >= required_exp


def filter_candidates(candidates: List[Dict], job: Dict):
    """
    Rule-based filtering:
    - Skills overlap
    - Experience threshold
    """

    filtered = []

    job_skills = job.get("required_skills", [])
    required_exp = job.get("min_experience", 0)

    for candidate in candidates:
        candidate_skills = candidate.get("skills", [])
        candidate_exp = candidate.get("experience_years", 0)

        if (
            has_skill_match(candidate_skills, job_skills) and
            has_experience_match(candidate_exp, required_exp)
        ):
            filtered.append(candidate)

    return filtered