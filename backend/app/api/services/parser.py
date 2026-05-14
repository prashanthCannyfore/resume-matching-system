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
    """
    Canonical skill normalization pipeline:
    1. Lowercase + strip
    2. Collapse whitespace
    3. Strip dots/hyphens ONLY for alias lookup (not for preserved names like node.js)
    4. Alias map → canonical name
    5. Multi-word phrase extraction (e.g. "react developer" → "react")

    Returns the canonical skill name used for all matching.
    """
    if not skill:
        return ""

    # Step 1-2: lowercase, collapse whitespace
    s = skill.lower().strip()
    s = re.sub(r"\s+", " ", s)

    # Step 3: version for alias lookup — strip dots/hyphens
    s_stripped = re.sub(r"[\.\-]", "", s)

    # ── Alias table (keyed on dot/hyphen-stripped form) ───────────────────────
    _ALIASES: dict[str, str] = {
        # JavaScript / React ecosystem
        "react":            "react",
        "reactjs":          "react",
        "reactjsx":         "react",
        "reactjs":          "react",
        "reactdeveloper":   "react",
        "reactdevelopment": "react",
        "reactfrontend":    "react",
        "frontendreact":    "react",
        "reactnative":      "react native",
        "nextjs":           "next.js",
        "vuejs":            "vue",
        "angularjs":        "angular",
        "nodejs":           "node.js",
        "nodejsdeveloper":  "node.js",
        "expressjs":        "express",
        "js":               "javascript",
        "javascript":       "javascript",
        "typescript":       "typescript",
        "ts":               "typescript",
        "es6":              "javascript",
        "es2015":           "javascript",
        "mern":             "react",      # MERN implies React
        "mernstack":        "react",
        "meanstack":        "angular",
        "fullstack":        "full stack",
        "fullstackdeveloper": "full stack",
        # CSS / styling
        "tailwindcss":      "tailwind",
        "bootstrap5":       "bootstrap",
        "materialui":       "mui",
        # Python
        "python3":          "python",
        # Java / JVM
        "java8":            "java",
        "springboot":       "spring boot",
        # .NET — handle BEFORE stripping dots
        "dotnet":           ".net",
        "aspnet":           "asp.net",
        "csharp":           "c#",
        # Databases
        "postgres":         "postgresql",
        "postgresqldb":     "postgresql",
        "mongo":            "mongodb",
        "mongodb":          "mongodb",
        "mssql":            "sql server",
        "microsoftsqlserver": "sql server",
        # Cloud / DevOps
        "amazonwebservices": "aws",
        "microsoftazure":   "azure",
        "googlecloud":      "gcp",
        "googlecloudplatform": "gcp",
        "k8s":              "kubernetes",
        "cicd":             "ci/cd",
        # Design tools
        "xd":               "adobe xd",
        "adobexd":          "adobe xd",
        "figma":            "figma",
        "sketch":           "sketch",
        "uxdesign":         "ux design",
        "uiux":             "ux design",
        "userexperience":   "ux design",
        "userexperiencedesign": "ux design",
        "photoshop":        "adobe photoshop",
        "adobephotoshop":   "adobe photoshop",
        "illustrator":      "adobe illustrator",
        "adobeillustrator": "adobe illustrator",
        "indesign":         "adobe indesign",
        "adobeindesign":    "adobe indesign",
        "aftereffects":     "adobe after effects",
        "adobeaftereffects": "adobe after effects",
        "brandidentity":    "brand identity",
        "visualidentity":   "brand identity",
        "digitalmarketing": "digital marketing",
        "mobileapp":        "mobile app",
        # Version control
        "github":           "git",
        "gitlab":           "git",
        "bitbucket":        "git",
        # Testing
        "jest":             "jest",
        "junit":            "junit",
        "selenium":         "selenium",
        "cypress":          "cypress",
        # REST / API
        "restapi":          "rest api",
        "restfulapi":       "rest api",
        "restful":          "rest api",
        "graphql":          "graphql",
    }

    # Check stripped form first
    if s_stripped in _ALIASES:
        return _ALIASES[s_stripped]

    # Check original (with dots/hyphens) for things like "node.js", "asp.net"
    _DOT_ALIASES: dict[str, str] = {
        "node.js":          "node.js",
        "node js":          "node.js",
        "express.js":       "express",
        "react.js":         "react",
        "vue.js":           "vue",
        "angular.js":       "angular",
        "next.js":          "next.js",
        "nuxt.js":          "nuxt.js",
        ".net":             ".net",
        "asp.net":          "asp.net",
        "ui/ux":            "ux design",
        "ui ux":            "ux design",
        "ci/cd":            "ci/cd",
        "rest api":         "rest api",
        "full stack":       "full stack",
        "full-stack":       "full stack",
        "spring boot":      "spring boot",
        "adobe xd":         "adobe xd",
        "adobe photoshop":  "adobe photoshop",
        "adobe illustrator": "adobe illustrator",
        "adobe indesign":   "adobe indesign",
        "adobe after effects": "adobe after effects",
        "brand identity":   "brand identity",
        "visual identity":  "brand identity",
        "digital marketing": "digital marketing",
        "mobile app":       "mobile app",
        "react native":     "react native",
        "user experience":  "ux design",
        "user experience design": "ux design",
        "amazon web services": "aws",
        "microsoft azure":  "azure",
        "google cloud":     "gcp",
        "google cloud platform": "gcp",
        "microsoft sql server": "sql server",
        "ms sql":           "sql server",
        "postgre sql":      "postgresql",
        "mongo db":         "mongodb",
        "material ui":      "mui",
        "tailwind css":     "tailwind",
        "java 8":           "java",
        "python 3":         "python",
        "dot net":          ".net",
        "asp net":          "asp.net",
        "c sharp":          "c#",
    }

    if s in _DOT_ALIASES:
        return _DOT_ALIASES[s]

    # ── Multi-word phrase extraction ──────────────────────────────────────────
    # "react developer" → "react", "senior react developer" → "react"
    # "python engineer" → "python", "node.js backend" → "node.js"
    _TECH_CORES = [
        "react", "angular", "vue", "node.js", "nodejs", "python", "java",
        "typescript", "javascript", "django", "fastapi", "flask", "spring",
        "kubernetes", "docker", "aws", "azure", "gcp", "postgresql", "mongodb",
        "redis", "graphql", "figma", "flutter", "swift", "kotlin", "golang",
        "rust", "scala", "php", "ruby", "rails",
    ]
    _NOISE_WORDS = {
        "developer", "engineer", "development", "programming", "senior",
        "junior", "lead", "architect", "specialist", "expert", "professional",
        "stack", "backend", "frontend", "fullstack", "full", "web", "mobile",
        "software", "application", "app", "framework", "library", "platform",
    }
    words = s.split()
    if len(words) > 1:
        # Extract tech core words from the phrase
        tech_words = [w for w in words if w not in _NOISE_WORDS]
        if len(tech_words) == 1:
            # Single tech word remains after stripping noise → normalize it
            return normalize_skill_name(tech_words[0])
        # Check if any known tech core is in the phrase
        for core in _TECH_CORES:
            if core in words or core.replace(".", "") in [w.replace(".", "") for w in words]:
                return normalize_skill_name(core)

    return s


def normalize_skill_list(skills: list[str]) -> list[str]:
    return [normalize_skill_name(skill) for skill in skills if skill]


async def extract_skills(text: str, db: AsyncSession = None):
    """
    Extract skills from resume/JD text.
    Pipeline:
    1. Try explicit Skills section first (most reliable)
    2. Scan full text for known skill keywords (including variants)
    3. Normalize everything through normalize_skill_name
    4. Deduplicate
    """
    # ── 1. Explicit skills section ────────────────────────────────────────────
    skills_section = extract_section(text, ["skills", "technical skills", "toolset", "expertise"])
    if skills_section:
        explicit_skills = parse_skills_from_section(skills_section)
        if explicit_skills:
            # Normalize and deduplicate
            normalized = list(dict.fromkeys(
                n for s in explicit_skills if s
                for n in [normalize_skill_name(s)] if n
            ))
            return normalized

    # ── 2. Full-text keyword scan ─────────────────────────────────────────────
    text_lower = text.lower()
    # Preserve dots for node.js, react.js etc. but normalize spaces
    text_clean = re.sub(r"\s+", " ", text_lower)

    found_canonical: set[str] = set()

    # Database skills
    if db:
        try:
            result = await db.execute(select(Skill.name))
            for skill_name in result.scalars().all():
                if skill_name.lower() in text_clean:
                    found_canonical.add(normalize_skill_name(skill_name))
        except Exception:
            pass

    # Comprehensive keyword list — includes all common variants
    # Each entry is scanned as a substring; normalize_skill_name maps to canonical
    _SCAN_KEYWORDS = [
        # React variants
        "react.js", "reactjs", "react js", "react native", "react",
        # Node variants
        "node.js", "nodejs", "node js",
        # Other JS
        "next.js", "nextjs", "nuxt.js", "vue.js", "vuejs", "angular",
        "javascript", "typescript", "redux", "graphql",
        # CSS/UI
        "tailwindcss", "tailwind", "bootstrap", "material ui", "mui",
        "html", "css", "sass", "scss",
        # Python
        "python", "django", "fastapi", "flask",
        # Java
        "spring boot", "springboot", "java",
        # .NET
        "asp.net", ".net", "c#",
        # Databases
        "postgresql", "postgres", "mysql", "mongodb", "redis",
        "sqlite", "sql server", "mssql",
        # Cloud/DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "k8s",
        "jenkins", "ci/cd", "terraform", "ansible",
        # Design
        "figma", "adobe xd", "sketch", "invision", "zeplin",
        "photoshop", "illustrator", "indesign", "after effects",
        "ui/ux", "ux design",
        # Version control
        "github", "gitlab", "bitbucket", "git",
        # Testing
        "jest", "cypress", "selenium", "junit",
        # Misc
        "rest api", "restful", "microservices",
        "mern", "mean", "full stack", "fullstack",
    ]

    for kw in _SCAN_KEYWORDS:
        # Use word-boundary-aware check to avoid "java" matching "javascript"
        # For single-word skills use word boundary; for multi-word use substring
        if " " in kw or "." in kw or "/" in kw:
            if kw in text_clean:
                found_canonical.add(normalize_skill_name(kw))
        else:
            # Word boundary check
            if re.search(rf"\b{re.escape(kw)}\b", text_clean):
                found_canonical.add(normalize_skill_name(kw))

    # Remove empty strings
    found_canonical.discard("")
    return sorted(found_canonical)


# def extract_total_experience(text: str):
#     if not text:
#         return 0

#     # 1. Explicit "Total Experience: X years" takes highest priority
#     total_match = re.search(
#         r"total\s+experience\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\+?\s*(?:years?|yrs?)",
#         text, re.I
#     )
#     if total_match:
#         try:
#             return float(total_match.group(1))
#         except ValueError:
#             pass

#     # 2. Explicit "X+ years of experience" / "X yrs exp" in profile summary
#     direct_match = re.search(
#         r"([0-9]+(?:\.[0-9]+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp(?:ertise)?)",
#         text, re.I
#     )
#     if direct_match:
#         try:
#             return float(direct_match.group(1))
#         except ValueError:
#             pass

#     # 2. Strip education section so graduation years don't pollute date ranges
#     work_text = text
#     edu_section = extract_section(text, ["education", "academic qualifications", "qualifications"])
#     if edu_section:
#         work_text = text.replace(edu_section, "")

#     # 3. Extract all date ranges with month-aware regex
#     #    Matches: "Jan 2020 – Present", "July 2025 - Dec 2025", "2020–2022"
#     date_range_pattern = re.compile(
#         r"((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
#         r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?\s*\d{4})"
#         r"\s*[–—\-]+\s*"
#         r"(present|current|now|"
#         r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
#         r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?\s*\d{4})",
#         re.I
#     )

#     raw_ranges = date_range_pattern.findall(work_text)
#     if not raw_ranges:
#         return 0

#     # 4. Convert to absolute month integers and collect valid intervals
#     intervals: list[tuple[int, int]] = []
#     for start_str, end_str in raw_ranges:
#         start = _parse_date_to_ym(start_str)
#         end = _parse_date_to_ym(end_str)
#         if start and end:
#             s_abs = start[0] * 12 + start[1]
#             e_abs = end[0] * 12 + end[1]
#             if e_abs > s_abs:
#                 intervals.append((s_abs, e_abs))

#     if not intervals:
#         return 0

#     # 5. Merge overlapping / adjacent intervals to avoid double-counting
#     #    e.g. [Dec 2023–Apr 2024] and [Mar 2024–Jun 2024] overlap by 1 month
#     intervals.sort()
#     merged: list[list[int]] = []
#     for s, e in intervals:
#         if merged and s <= merged[-1][1]:
#             merged[-1][1] = max(merged[-1][1], e)
#         else:
#             merged.append([s, e])

#     total_months = sum(e - s for s, e in merged)
#     return round(total_months / 12, 1)

def extract_total_experience(text: str) -> float:
    if not text:
        return 0.0

    text_lower = text.lower()

    # ====================== PRIORITY 1: EXPLICIT MENTIONS (Most Accurate) ======================
    explicit_patterns = [
        r"total\s+experience\s*[:\-]?\s*(\d+\.?\d*)\+?\s*(?:years?|yrs?)",
        r"(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:total|overall)?\s*experience",
        r"(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:exp|experience)",
        r"(\d+\.?\d*)\+?\s*years?\s*(?:of)?\s*experience",
        r"experience\s*[:\-]?\s*(\d+\.?\d*)\+?\s*(?:years?|yrs?)",
    ]

    for pattern in explicit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return round(float(match.group(1)), 1)
            except:
                continue

    # ====================== PRIORITY 2: SIMPLE "X YEARS" / "X YRS EXP" ======================
    simple_match = re.search(r"(\d+\.?\d*)\+?\s*(?:years?|yrs?)\b", text_lower)
    if simple_match:
        try:
            years = float(simple_match.group(1))
            if 0 < years <= 30:   # Reasonable limit
                return round(years, 1)
        except:
            pass

    # ====================== FALLBACK: DATE RANGE CALCULATION (Conservative) ======================
    # Remove education section to avoid pollution
    edu_section = extract_section(text, ["education", "academic qualifications", "qualifications"])
    work_text = text.replace(edu_section, "") if edu_section else text

    date_range_pattern = re.compile(
        r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}|\d{4})\s*"
        r"[–—-]\s*"
        r"(present|current|now|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}|\d{4})",
        re.I
    )

    raw_ranges = date_range_pattern.findall(work_text)
    if not raw_ranges:
        return 0.0

    intervals = []
    for start_str, end_str in raw_ranges:
        start = _parse_date_to_ym(start_str)
        end = _parse_date_to_ym(end_str)
        if start and end:
            s_abs = start[0] * 12 + start[1]
            e_abs = end[0] * 12 + end[1]
            if e_abs > s_abs + 3:   # at least 3 months
                intervals.append((s_abs, e_abs))

    if not intervals:
        return 0.0

    # Merge overlapping/adjacent intervals with gap tolerance
    intervals.sort()
    merged = []
    for current in intervals:
        if not merged or merged[-1][1] + 12 < current[0]:   # >1 year gap = new period
            merged.append(list(current))
        else:
            merged[-1][1] = max(merged[-1][1], current[1])

    total_months = sum(e - s for s, e in merged)
    calculated = round(total_months / 12, 1)

    # Safety: Don't return unrealistically high values
    return calculated if calculated <= 30 else 0.0

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