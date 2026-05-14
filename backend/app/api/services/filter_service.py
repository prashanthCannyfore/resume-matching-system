"""
Hybrid filter + rank service.

Scoring weights (revised):
  70% skill match  — primary signal, most reliable
  20% semantic similarity — FAISS cosine, secondary
  10% experience match — tertiary

Hard cap: if required skills exist and candidate matches NONE of them,
final_score is capped at 0.30 so irrelevant profiles never outrank
relevant ones purely on semantic similarity.
"""
import logging
from typing import List, Dict

from app.api.services.parser import normalize_skill_list

logger = logging.getLogger(__name__)

# ── Weights ───────────────────────────────────────────────────────────────────
SKILL_WEIGHT      = 0.70   # dominant — exact/normalized skill overlap
SIMILARITY_WEIGHT = 0.20   # semantic FAISS cosine
EXPERIENCE_WEIGHT = 0.10   # years of experience

# Candidates with 0 skill match are capped here (prevents graphic designer
# ranking above React dev on a React JD due to semantic similarity alone)
ZERO_SKILL_SCORE_CAP = 0.30

MIN_SCORE_THRESHOLD = 0.05   # only exclude truly irrelevant (near-zero)


def calculate_skill_score(
    candidate_skills: List[str],
    job_skills: List[str],
) -> tuple[float, list[str], list[str]]:
    """
    Returns (score 0-1, matched_list, missing_list).
    Both lists contain canonical normalized skill names.
    """
    if not job_skills:
        return 0.0, [], []

    norm_candidate = set(normalize_skill_list(candidate_skills))
    norm_job       = set(normalize_skill_list(job_skills))

    # Remove empty strings that normalization might produce
    norm_candidate.discard("")
    norm_job.discard("")

    if not norm_job:
        return 0.0, [], []

    matched = sorted(norm_candidate & norm_job)
    missing = sorted(norm_job - norm_candidate)
    score   = round(len(matched) / len(norm_job), 3)

    logger.debug(
        f"[skill_score] required={sorted(norm_job)} "
        f"candidate={sorted(norm_candidate)} "
        f"matched={matched} missing={missing} score={score}"
    )
    return score, matched, missing


def filter_and_rank_candidates(
    candidates: List[Dict],
    job: Dict,
    similarity_results: List[Dict],
) -> List[Dict]:
    job_skills   = job.get("required_skills", [])
    required_exp = job.get("min_experience", 0)
    has_required_skills = bool(normalize_skill_list(job_skills))

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
        candidate_exp    = candidate.get("experience_years", 0)

        skill_score, matched_skills, missing_skills = calculate_skill_score(
            candidate_skills, job_skills
        )

        # Hard-block: 0 experience when job explicitly requires some
        if required_exp > 0 and candidate_exp == 0:
            continue

        similarity_score = similarity_map[cid]

        # Experience match ratio (0-1)
        if required_exp == 0:
            exp_match = 1.0
        elif candidate_exp >= required_exp:
            exp_match = 1.0
        else:
            exp_match = round(candidate_exp / required_exp, 3)

        # Weighted score
        raw_score = round(
            SKILL_WEIGHT      * skill_score
            + SIMILARITY_WEIGHT * similarity_score
            + EXPERIENCE_WEIGHT * exp_match,
            3,
        )

        # Hard cap: zero skill match on a JD that has required skills
        if has_required_skills and skill_score == 0.0:
            raw_score = min(raw_score, ZERO_SKILL_SCORE_CAP)

        if raw_score < MIN_SCORE_THRESHOLD:
            continue

        candidate["score"]          = raw_score
        candidate["similarity"]     = similarity_score
        candidate["skill_score"]    = skill_score
        candidate["matched_skills"] = matched_skills
        candidate["missing_skills"] = missing_skills

        logger.info(
            f"[filter] id={cid} name={candidate.get('name','?')!r} | "
            f"skill={skill_score:.2f} sim={similarity_score:.3f} "
            f"exp={exp_match:.2f} score={raw_score:.3f} | "
            f"matched={matched_skills} missing={missing_skills}"
        )

        final_results.append(candidate)

    return sorted(final_results, key=lambda x: x["score"], reverse=True)
