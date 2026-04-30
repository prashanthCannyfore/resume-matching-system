import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.models.skill import Skill


def normalize_text(text: str) -> str:
    text = text.lower()

    # remove special characters (commas, dots, etc.)
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


async def extract_skills(text: str, db: AsyncSession = None):
    text = normalize_text(text)

    found_skills = []

    if db:
        try:
            result = await db.execute(select(Skill.name))
            common_skills = result.scalars().all()

            for skill in common_skills:
                skill_clean = normalize_text(skill)

                if f" {skill_clean} " in f" {text} ":
                    found_skills.append(skill_clean)

            return list(set(found_skills))

        except Exception:
            pass  # fallback if DB fails

    # fallback skills
    fallback_skills = ["python", "java", "sql", "fastapi", "django"]

    for skill in fallback_skills:
        if f" {skill} " in f" {text} ":
            found_skills.append(skill)

    return list(set(found_skills))


def extract_total_experience(text: str):
    text = normalize_text(text)

    matches = re.findall(r"(\d+)\+?\s*(?:years|yrs)", text)

    return max(map(int, matches)) if matches else 0


def extract_company(text: str) -> str | None:
    match = re.search(r"company[:\s]*([^\n\r]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_location(text: str) -> str | None:
    match = re.search(r"location[:\s]*([^\n\r]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


async def extract_skill_experience(text: str, db: AsyncSession):
    text = normalize_text(text)

    result = await db.execute(select(Skill.name))
    common_skills = result.scalars().all()

    skill_experience = []

    for skill in common_skills:
        pattern = rf"({skill}).{{0,50}}?(\d+)\+?\s*(?:years|yrs)|(\d+)\+?\s*(?:years|yrs).{{0,50}}?({skill})"
        matches = re.findall(pattern, text)

        for match in matches:
            numbers = [m for m in match if m.isdigit()]
            if numbers:
                skill_experience.append({"skill": skill, "experience": int(numbers[0])})

    return skill_experience


def extract_education(text: str):
    text = text.lower()

    match = re.search(
        r"\b(bachelor|master|phd|ph\.d|doctor|diploma|associate|certificate)\b", text
    )
    if match:
        degree = match.group(1)
        if degree in ["phd", "ph.d", "doctor"]:
            return "PhD"
        elif degree == "bachelor":
            return "Bachelor"
        elif degree == "master":
            return "Master"
        elif degree == "diploma":
            return "Diploma"
    else:
        # If no standard degree, try to extract mentioned education
        edu_match = re.search(
            r"(?:education|degree|qualification)[:\s]*([^\n\r]+)", text, re.IGNORECASE
        )
        if edu_match:
            return f"Other-{edu_match.group(1).strip()}"
    return None


def extract_email(text: str) -> str | None:
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    if match:
        return match.group(0)
    return None
