from app.api.services.file_service import validate_file, save_file, extract_text
from app.api.services.parser import (
    extract_skills,
    extract_total_experience,
    extract_education,
    extract_skill_experience
)

async def process_resume(file: UploadFile, db: AsyncSession):
    validate_file(file)

    file_path = await save_file(file)
    text = extract_text(file_path)

    skills = extract_skills(text)
    experience = extract_total_experience(text)
    education = extract_education(text)
    skill_exp = extract_skill_experience(text)

    candidate = Candidate(
        name=file.filename,
        email=f"{file.filename}@temp.com",
        skills=skills,
        experience_years=experience,
        education=education,
        resume_text=text
    )

    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    return {
        "candidate": candidate,
        "skill_experience": skill_exp
    }