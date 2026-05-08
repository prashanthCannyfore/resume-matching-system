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
    """Parse a date string like 'Jan 2020', '2020', 'Present' into (year, month)."""
    s = date_str.strip().lower()
    if s in ("present", "current", "now"):
        now = datetime.now()
        return (now.year, now.month)
    # Try "Month YYYY" or "YYYY Month"
    for month_name, month_num in MONTH_MAP.items():
        pattern = rf"\b{month_name}\b"
        if re.search(pattern, s):
            year_match = re.search(r"\b(\d{{4}})\b", s)
            if year_match:
                return (int(year_match.group(1)), month_num)
    # Plain year only
    year_match = re.search(r"\b(\d{4})\b", s)
    if year_match:
        return (int(year_match.group(1)), 6)  # assume mid-year if no month
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


def parse_skills_from_section(section_text: str):
    if not section_text:
        return []

    cleaned = []
    for line in section_text.splitlines():
        if ":" in line:
            _, line = line.split(":", 1)
        line = line.replace("•", ",").replace("·", ",").replace("|", ",")
        parts = re.split(r"[,;/\\]+", line)
        for part in parts:
            skill = part.strip().strip(".\\")
            if skill:
                cleaned.append(skill)

    return list(dict.fromkeys(cleaned))


def normalize_skill_name(skill: str) -> str:
    if not skill:
        return ""
    normalized = skill.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)

    aliases = {
        "xd": "adobe xd",
        "adobe xd": "adobe xd",
        "figma": "figma",
        "ux design": "ux design",
        "ui/ux": "ux design",
        "ui ux": "ux design",
        "user experience": "ux design",
        "photoshop": "adobe photoshop",
        "illustrator": "adobe illustrator",
        "indesign": "adobe indesign",
        "after effects": "adobe after effects",
        "adobe after effects": "adobe after effects",
        "brand identity": "brand identity",
        "typography": "typography",
        "digital marketing": "digital marketing",
        "mobile app": "mobile app",
        "visual identity": "brand identity",
    }

    if normalized in aliases:
        return aliases[normalized]

    return normalized


def normalize_skill_list(skills: list[str]) -> list[str]:
    return [normalize_skill_name(skill) for skill in skills if skill]


async def extract_skills(text: str, db: AsyncSession = None):
    skills_section = extract_section(text, ["skills", "technical skills", "toolset", "expertise"])
    if skills_section:
        explicit_skills = parse_skills_from_section(skills_section)
        if explicit_skills:
            return explicit_skills

    text_lower = normalize_text(text)
    found_skills = set()

    # Database skills
    if db:
        try:
            result = await db.execute(select(Skill.name))
            common_skills = [s.lower() for s in result.scalars().all()]
            for skill in common_skills:
                if skill in text_lower:
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
        if skill in text_lower:
            found_skills.add(skill)

    return list(found_skills)


def extract_total_experience(text: str):
    if not text:
        return 0

    # 1. Try explicit "X years of experience" statement first
    direct_match = re.search(r"total experience\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:years?|yrs?)", text, re.I)
    if not direct_match:
        direct_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)", text, re.I)
    if direct_match:
        try:
            return float(direct_match.group(1))
        except ValueError:
            pass

    # 2. Extract work experience section only (exclude education dates)
    work_text = text
    edu_section = extract_section(text, ["education", "academic qualifications", "qualifications"])
    if edu_section:
        work_text = text.replace(edu_section, "")

    # 3. Month-aware date range parsing
    # Matches: "Jan 2020 – Present", "January 2020 - 2022", "2020 – Present", "2018–2020"
    date_range_pattern = re.compile(
        r"((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?\s*\d{4})"
        r"\s*[–—\-]+\s*"
        r"(present|current|now|"
        r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?\s*\d{4})",
        re.I
    )

    ranges = date_range_pattern.findall(work_text)
    total_months = 0

    for start_str, end_str in ranges:
        start = _parse_date_to_ym(start_str)
        end = _parse_date_to_ym(end_str)
        if start and end:
            months = (end[0] - start[0]) * 12 + (end[1] - start[1])
            if months > 0:
                total_months += months

    if total_months:
        return round(total_months / 12, 1)

    return 0


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
        ("UI/UX Design", "ui/ux"),
        ("Brand Identity", "brand identity"),
        ("Typography", "typography"),
        ("Digital Marketing", "digital marketing"),
        ("Mobile App UI/UX", "mobile app"),
        ("Visual Identity", "visual identities"),
        ("Campaign Design", "campaign"),
        ("Social Media Design", "social media"),
    ]
    return [label for label, keyword in candidates if keyword in text_lower]


def extract_design_tools(skills: list[str]):
    tool_keywords = ["adobe", "figma", "xd", "after effects", "photoshop", "illustrator", "indesign", "sketch"]
    return [skill for skill in skills if any(keyword in skill.lower() for keyword in tool_keywords)]


def extract_additional_strengths(text: str):
    strengths = []
    text_lower = text.lower()
    brand_match = re.search(r"(\d+\+?\s*brands?[^\n]*)", text_lower)
    if brand_match:
        strengths.append(brand_match.group(1).strip().capitalize())
    reach_match = re.search(r"(\d+\+?\s*m(?:illion)?\+?\s*(?:impressions|reach|views)[^\n]*)", text_lower)
    if reach_match:
        strengths.append(reach_match.group(1).strip().capitalize())
    if "mentored" in text_lower or "mentoring" in text_lower:
        strengths.append("Mentoring and team leadership experience")
    if "mobile app" in text_lower:
        strengths.append("Experience designing mobile app user interfaces")
    if "campaign" in text_lower and "led" in text_lower:
        strengths.append("Led campaigns with measurable reach or impact")
    if any(word in text_lower for word in ["fmcg", "tech", "hospitality"]):
        strengths.append("Domain exposure across multiple industries")

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
        "🧑‍💼 Experience\n"
        f"Total Experience: {total_experience} years\n"
        "Timeline:\n"
        f"{timeline_text}\n\n"
        "🎯 Key Skills\n"
        f"Design Tools: {design_text}\n"
        "Core Areas:\n"
        f"{core_text}\n\n"
        "💡 Additional Strengths\n"
        f"{strengths_text}\n\n"
        "🎓 Education\n"
        f"{education}"
    )


def extract_email(text: str):
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    return match.group(0) if match else None