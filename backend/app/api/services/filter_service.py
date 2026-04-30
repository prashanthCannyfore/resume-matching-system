from typing import List, Dict

# -------------------------
# CONFIG
# -------------------------
SIMILARITY_WEIGHT = 0.7
SKILL_WEIGHT = 0.3
MIN_SCORE_THRESHOLD = 0.1


# -------------------------
# SKILL MATCH SCORE
# -------------------------
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
    candidates: List[Dict], job: Dict, similarity_results: List[Dict]
):
    job_skills = job.get("required_skills", [])
    required_exp = job.get("min_experience", 0)

    similarity_map = {
        item["candidate_id"]: item["similarity"] for item in similarity_results
    }

    final_results = []

    for candidate in candidates:
        cid = candidate.get("id")

        # Skip if not in similarity results
        if cid not in similarity_map:
            continue

        candidate_skills = candidate.get("skills", [])
        candidate_exp = candidate.get("experience_years", 0)

        # Skill score
        skill_score = calculate_skill_score(candidate_skills, job_skills)

        # Experience filter
        if not has_experience_match(candidate_exp, required_exp):
            continue

        similarity_score = similarity_map[cid]

        # Final hybrid score
        final_score = round(
            (SIMILARITY_WEIGHT * similarity_score) + (SKILL_WEIGHT * skill_score), 3
        )

        # Apply threshold filter
        if final_score < MIN_SCORE_THRESHOLD:
            continue

        candidate["score"] = final_score
        candidate["similarity"] = similarity_score
        candidate["skill_score"] = skill_score

        final_results.append(candidate)

    # Sort descending
    return sorted(final_results, key=lambda x: x["score"], reverse=True)
