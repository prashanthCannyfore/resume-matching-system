from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.api.models.job import JobDescription
from app.api.services.file_service import extract_text, save_file, validate_file
from app.api.services.parser import extract_skills, extract_total_experience

async def process_job_description(file: UploadFile, db: AsyncSession):
    validate_file(file)

    file_path = await save_file(file)
    text = extract_text(file_path)

    skills = extract_skills(text)
    experience = extract_total_experience(text)

    job = JobDescription(
        title=file.filename,
        company="",
        location="",
        required_skills=skills,
        min_experience=experience,
        description_text=text
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    return job


# ✅ MANUAL JSON INPUT FLOW 
async def create_job(data, db: AsyncSession):
    skills = extract_skills(data.description_text)
    experience = extract_total_experience(data.description_text)

    job = JobDescription(
        title=data.title,
        company=data.company,
        location=data.location,
        required_skills=skills,
        min_experience=experience,
        required_education=data.required_education,
        description_text=data.description_text
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    return job