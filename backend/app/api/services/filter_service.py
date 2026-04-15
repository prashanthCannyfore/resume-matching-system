from typing import List, Dict



def calculate_skill_score(candidate_skills: List[str], job_skills: List[str]):
    if not job_skills:
        return 0

    match_count = len(set(candidate_skills) & set(job_skills))
    return round(match_count / len(job_skills), 2)


# -------------------------
# EXPERIENCE CHECK
# -------------------------
def has_experience_match(candidate_exp: int, required_exp: int):
    return candidate_exp >= required_exp


# -------------------------
# HYBRID FILTER + RANK
# -------------------------
def filter_and_rank_candidates(
    candidates: List[Dict],
    job: Dict,
    similarity_results: List[Dict]
):
    job_skills = job.get("required_skills", [])
    required_exp = job.get("min_experience", 0)

    similarity_map = {
        item["candidate_id"]: item["similarity"]
        for item in similarity_results
    }

    final_results = []

    for candidate in candidates:
        cid = candidate.get("id")

        if cid not in similarity_map:
            continue

        candidate_skills = candidate.get("skills", [])
        candidate_exp = candidate.get("experience_years", 0)

        skill_score = calculate_skill_score(candidate_skills, job_skills)

        if not has_experience_match(candidate_exp, required_exp):
            continue

        similarity_score = similarity_map[cid]

        #  HYBRID SCORE
        final_score = round(
            (0.7 * similarity_score) + (0.3 * skill_score),
            3
        )

        candidate["score"] = final_score
        candidate["similarity"] = similarity_score
        candidate["skill_score"] = skill_score

        final_results.append(candidate)

    return sorted(final_results, key=lambda x: x["score"], reverse=True)