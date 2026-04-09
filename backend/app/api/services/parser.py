import re

COMMON_SKILLS = [
    "python", "java", "sql", "fastapi", "docker",
    "kubernetes", "aws", "react", "vue", "node"
]


def normalize_text(text: str) -> str:
    return text.lower().strip()


def extract_skills(text: str):
    text = normalize_text(text)

    found_skills = []
    for skill in COMMON_SKILLS:
        if re.search(rf"\b{skill}\b", text):
            found_skills.append(skill)

    return list(set(found_skills))


def extract_total_experience(text: str):
    text = normalize_text(text)

    matches = re.findall(r'(\d+)\+?\s*(?:years|yrs)', text)

    return max(map(int, matches)) if matches else 0


def extract_skill_experience(text: str):
    text = normalize_text(text)

    skill_experience = []

    for skill in COMMON_SKILLS:
        pattern = rf"({skill}).{{0,50}}?(\d+)\+?\s*(?:years|yrs)|(\d+)\+?\s*(?:years|yrs).{{0,50}}?({skill})"
        matches = re.findall(pattern, text)

        for match in matches:
            numbers = [m for m in match if m.isdigit()]
            if numbers:
                skill_experience.append({
                    "skill": skill,
                    "experience": int(numbers[0])
                })

    return skill_experience


def extract_education(text: str):
    text = text.lower()

    if "bachelor" in text:
        return "Bachelor"
    if "master" in text:
        return "Master"
    if "phd" in text:
        return "PhD"

    return None