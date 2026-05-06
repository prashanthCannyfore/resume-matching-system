import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.models.skill import Skill

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s+]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def extract_skills(text: str, db: AsyncSession = None):
    text = normalize_text(text)
    found_skills = set()

    # Database skills
    if db:
        try:
            result = await db.execute(select(Skill.name))
            common_skills = [s.lower() for s in result.scalars().all()]
            for skill in common_skills:
                if skill in text:
                    found_skills.add(skill)
        except:
            pass

    # Very comprehensive fallback for resumes
    fallback_skills = [
        "react", "reactjs", "nodejs", "node.js", "javascript", "typescript", "redux", "vue", "angular",
        "bootstrap", "mui", "tailwind", "html", "css", "python", "java", "c#", ".net", "asp.net",
        "sql", "mysql", "postgresql", "mongodb", "redis", "aws", "azure", "docker", "kubernetes",
        "git", "jenkins", "ci/cd", "microservices", "rest api", "figma", "adobe xd", "ui/ux", "ux design"
    ]

    for skill in fallback_skills:
        if skill in text:
            found_skills.add(skill)

    return list(found_skills)


def extract_total_experience(text: str):
    if not text:
        return 0

    text = normalize_text(text)

    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?|exp|experience)",
        r"(\d+)\s*years?",
        r"over\s*(\d+)",
        r"(\d+)\+?\s*years?\s*of\s*exp"
    ]

    max_exp = 0
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            try:
                exp = int(m)
                if exp > max_exp:
                    max_exp = exp
            except:
                pass
    return max_exp


def extract_education(text: str):
    text_lower = text.lower()
    if "master" in text_lower or "mepco" in text_lower:
        return "Master’s Degree"
    if "bachelor" in text_lower or "kalasalingam" in text_lower:
        return "Bachelor’s Degree"
    if any(word in text_lower for word in ["b.e", "btech", "b.tech", "bca", "mca"]):
        return "Bachelor’s Degree"
    return "Not mentioned"


async def extract_skill_experience(text: str, db: AsyncSession):
    return []


def extract_email(text: str):
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    return match.group(0) if match else None