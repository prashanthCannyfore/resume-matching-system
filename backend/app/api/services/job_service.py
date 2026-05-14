from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.api.models.job import JobDescription
from app.api.services.file_service import extract_text, save_file, validate_file
from app.api.services.parser import (
    extract_skills,
    extract_total_experience,
    extract_education,
)
from app.api.services.embedding_service import generate_embedding_async
from app.api.services.vector_store import search_similar


async def process_job_description(file: UploadFile, db: AsyncSession):
    validate_file(file)
    file_path = await save_file(file)
    text = extract_text(file_path)

    skills = await extract_skills(text, db)
    experience = extract_total_experience(text)
    education = extract_education(text)
    embedding = await generate_embedding_async(text)

    job = JobDescription(
        title=file.filename,
        company="N/A",
        location="N/A",
        required_skills=skills,
        min_experience=experience,
        required_education=education,
        description_text=text,
        embedding=json.dumps(embedding),
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    return {
        "id": job.id,
        "title": job.title,
        "skills": skills,
        "experience": experience,
        "education": education,
    }


async def create_job(data, db: AsyncSession):
    skills = await extract_skills(data.description_text, db)
    experience = extract_total_experience(data.description_text)
    education = extract_education(data.description_text)
    embedding = await generate_embedding_async(data.description_text)

    job = JobDescription(
        title=data.title,
        company=getattr(data, "company", "N/A"),
        location=getattr(data, "location", "N/A"),
        required_skills=skills,
        min_experience=experience,
        required_education=education,
        description_text=data.description_text,
        embedding=json.dumps(embedding),
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    return {
        "id": job.id,
        "title": job.title,
        "skills": skills,
        "experience": experience,
        "education": education,
    }


async def find_similar_candidates(job_description: str):
    embedding = await generate_embedding_async(job_description)
    results = search_similar(embedding, top_k=5)
    return {"matches": results}
