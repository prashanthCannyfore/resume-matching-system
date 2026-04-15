from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.services.file_service import validate_file, save_file, extract_text
from app.api.services.parser import (
    extract_skills,
    extract_total_experience,
    extract_education,
    extract_skill_experience,
    extract_email
)
from app.api.models.candidate import Candidate


async def process_resume(file: UploadFile, db: AsyncSession):
    # -------------------------
    # VALIDATE + SAVE FILE
    # -------------------------
    validate_file(file)
    file_path = await save_file(file)

    # -------------------------
    # EXTRACT TEXT
    # -------------------------
    text = extract_text(file_path)

    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    # -------------------------
    # PARSING
    # -------------------------
    skills = await extract_skills(text, db)
    experience = extract_total_experience(text)
    education = extract_education(text)
    skill_exp = await extract_skill_experience(text, db)
    email = extract_email(text)

    # fallback email
    if not email:
        email = f"{file.filename}@temp.com"

    # -------------------------
    # SAVE TO DB
    # -------------------------
    candidate = Candidate(
        name=file.filename,   # later improve via NLP
        email=email,
        skills=skills,
        experience_years=experience,
        education=education,
        resume_text=text
    )

    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    # -------------------------
    # RESPONSE
    # -------------------------
    return {
        "candidate": candidate,
        "skill_experience": skill_exp
    }