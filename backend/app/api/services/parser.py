import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.models.skill import Skill

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

def _parse_date_to_ym(date_str: str):
    s = date_str.strip().lower()
    if s in ("present", "current", "now"):
        now = datetime.now()
        return (now.year, now.month)
    for month_name, month_num in MONTH_MAP.items():
        pattern = rf"\b{month_name}\b"
        if re.search(pattern, s):
            year_match = re.search(r"\b(\d{4})\b", s)
            if year_match:
                return (int(year_match.group(1)), month_num)
    year_match = re.search(r"\b(\d{4})\b", s)
    if year_match:
        return (int(year_match.group(1)), 6)
    return None


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\.\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_section(text: str, headers):
    if not text:
        return ""
    lines = text.splitlines()
    start = -1
    section_lines = []

    for i, line in enumerate(lines):
        normalized = line.strip().lower()
        for header in headers:
            if normalized.startswith(header):
                content = re.sub(rf"^\s*{header}\s*[:\-–—]?\s*", "", line.strip(), flags=re.I)
                if content:
                    section_lines.append(content.strip())
                start = i + 1
                break
        if start != -1:
            break

    if start == -1:
        return ""

    for line in lines[start:]:
        if not line.strip():
            if section_lines:
                break
            continue
        if re.match(r"^\s*(experience|professional experience|work experience|education|academic qualifications|qualifications|projects|certifications|summary|profile)\b", line, re.I):
            break
        section_lines.append(line.strip())

    return "\n".join(section_lines).strip()


def parse_skills_from_section(section_text: str) -> list[str]:
    if not section_text:
        return []
    cleaned = []
    for line in section_text.splitlines():
        if ":" in line:
            _, line = line.split(":", 1)
        line = line.replace("•", ",").replace("·", ",").replace("|", ",")
        parts = re.split(r"[,;/\\]+", line)
        for part in parts:
            skill = part.strip().strip(".\\").strip()
            if not skill:
                continue
            if len(skill.split()) > 5:
                continue
            lower = skill.lower()
            if any(lower.startswith(p) for p in ("certification in", "certified", "experience in", "knowledge of", "proficient in", "expertise in", "hands-on", "skilled in")):
                continue
            cleaned.append(skill)
    return list(dict.fromkeys(cleaned))


# ====================== SKILL NORMALIZATION ======================
def normalize_skill_name(skill: str) -> str:
    if not skill:
        return ""

    s = skill.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s_stripped = re.sub(r"[\.\-]", "", s)

    # Strong React matching
    react_keywords = {"react", "reactjs", "react.js", "react js", "mern", "mernstack", "nextjs", "next.js"}
    if any(k in s_stripped or k in s for k in react_keywords):
        return "react"

    ALIASES = {
        "reactjs": "react", "react.js": "react", "react js": "react", "mern": "react",
        "mernstack": "react", "nextjs": "react", "next.js": "react",
        "nodejs": "node.js", "node.js": "node.js", "node js": "node.js",
        "javascript": "javascript", "typescript": "typescript",
        "vuejs": "vue", "angularjs": "angular",
        "python3": "python", "java8": "java",
        "postgres": "postgresql", "mongo": "mongodb",
        "xd": "adobe xd", "ui/ux": "ux design", "ui ux": "ux design",
    }

    if s in ALIASES:
        return ALIASES[s]
    if s_stripped in ALIASES:
        return ALIASES[s_stripped]

    return s


def normalize_skill_list(skills: list[str]) -> list[str]:
    normalized = [normalize_skill_name(skill) for skill in skills if skill]
    return list(dict.fromkeys(normalized))


async def extract_skills(text: str, db: AsyncSession = None):
    if not text:
        return []

    skills_section = extract_section(text, ["skills", "technical skills", "toolset", "expertise", "technologies"])
    if skills_section:
        explicit = parse_skills_from_section(skills_section)
        if explicit:
            return normalize_skill_list(explicit)

    text_lower = normalize_text(text)
    found = set()

    if any(x in text_lower for x in ["react", "reactjs", "react.js", "mern", "next.js", "nextjs"]):
        found.add("react")

    scan_list = ["node.js", "nodejs", "python", "javascript", "typescript", "vue", "angular", "django", "fastapi", "aws"]
    for kw in scan_list:
        if kw in text_lower:
            found.add(normalize_skill_name(kw))

    if db:
        try:
            result = await db.execute(select(Skill.name))
            for skill_name in result.scalars().all():
                if skill_name.lower() in text_lower:
                    found.add(normalize_skill_name(skill_name))
        except:
            pass

    return sorted(list(found))


def extract_total_experience(text: str) -> float:
    if not text:
        return 0.0

    text_lower = text.lower()
    explicit_patterns = [
        r"total\s+experience\s*[:\-]?\s*(\d+\.?\d*)\+?\s*(?:years?|yrs?)",
        r"(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:total|overall)?\s*experience",
        r"(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:exp|experience)",
    ]

    for pattern in explicit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return round(float(match.group(1)), 1)
            except:
                continue

    simple_match = re.search(r"(\d+\.?\d*)\+?\s*(?:years?|yrs?)\b", text_lower)
    if simple_match:
        try:
            years = float(simple_match.group(1))
            if 0 < years <= 30:
                return round(years, 1)
        except:
            pass
    return 0.0


def extract_education(text: str):
    edu_section = extract_section(text, ["education", "academic qualifications", "qualifications"])
    if edu_section:
        lines = [line.strip() for line in edu_section.splitlines() if line.strip()]
        if len(lines) >= 2:
            return f"{lines[0]} | {lines[1]}"
        return lines[0]

    text_lower = text.lower()
    if "b.des" in text_lower:
        degree_match = re.search(r"(b\.des[^\n]*)", text, re.I)
        school_match = re.search(r"(nid[^\n]*)", text, re.I)
        if degree_match and school_match:
            return f"{degree_match.group(1).strip()} | {school_match.group(1).strip()}"
    if "master" in text_lower or "mepco" in text_lower:
        return "Master’s Degree"
    if "bachelor" in text_lower or "kalasalingam" in text_lower or any(word in text_lower for word in ["b.e", "btech", "b.tech", "bca", "mca"]):
        return "Bachelor’s Degree"
    return "Not mentioned"


async def extract_skill_experience(text: str, db: AsyncSession):
    skills = await extract_skills(text, db)
    return [{"skill": skill, "experience": ""} for skill in skills]


def extract_experience_timeline(text: str):
    experience_section = extract_section(text, ["experience", "professional experience", "work experience"])
    if not experience_section:
        return []
    timeline = []
    lines = [line.strip() for line in experience_section.splitlines() if line.strip()]
    for line in lines:
        match = re.match(r"(.+?)\s*\|\s*(\d{4})\s*[–—-]\s*(present|current|\d{4})(.*)", line, re.I)
        if match:
            title = match.group(1).strip()
            date_range = f"{match.group(2)} – {match.group(3)}"
            timeline.append(f"{title} ({date_range})")
        else:
            timeline.append(line)
    return timeline


def extract_core_areas(text: str):
    text_lower = text.lower()
    candidates = [
        ("UI/UX Design", "ui/ux"), ("Brand Identity", "brand identity"),
        ("Typography", "typography"), ("Digital Marketing", "digital marketing"),
    ]
    return [label for label, keyword in candidates if keyword in text_lower]


def extract_design_tools(skills: list[str]):
    tool_keywords = ["adobe", "figma", "xd", "after effects", "photoshop", "illustrator", "indesign", "sketch"]
    return [skill for skill in skills if any(keyword in skill.lower() for keyword in tool_keywords)]


def extract_additional_strengths(text: str):
    strengths = []
    text_lower = text.lower()
    if re.search(r"\d+\+?\s*brands?", text_lower):
        strengths.append("Work with multiple brands")
    if "mentored" in text_lower or "mentoring" in text_lower:
        strengths.append("Mentoring and team leadership")
    if any(word in text_lower for word in ["fmcg", "tech", "hospitality"]):
        strengths.append("Domain exposure")
    return list(dict.fromkeys(strengths))


async def generate_resume_insight(text: str, db: AsyncSession = None) -> str:
    skills = await extract_skills(text, db)
    total_experience = extract_total_experience(text)
    timeline = extract_experience_timeline(text)
    education = extract_education(text)
    design_tools = extract_design_tools(skills)
    core_areas = extract_core_areas(text)
    strengths = extract_additional_strengths(text)

    timeline_text = "\n".join(timeline) if timeline else "Not available"
    design_text = ", ".join(design_tools) if design_tools else ", ".join(skills)
    core_text = "\n".join(core_areas) if core_areas else "Not available"
    strengths_text = "\n".join(f"- {item}" for item in strengths) if strengths else "- Not enough explicit accomplishments extracted"

    return (
        "Here’s a quick breakdown of the candidate:\n\n"
        f"🧑‍💼 Experience\nTotal Experience: {total_experience} years\n"
        f"Timeline:\n{timeline_text}\n\n"
        f"🎯 Key Skills\nDesign Tools: {design_text}\n"
        f"Core Areas:\n{core_text}\n\n"
        f"💡 Additional Strengths\n{strengths_text}\n\n"
        f"🎓 Education\n{education}"
    )


def extract_email(text: str):
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    return match.group(0) if match else None