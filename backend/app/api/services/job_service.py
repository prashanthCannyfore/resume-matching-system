from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
import json

from app.api.models.job import JobDescription
from app.api.services.file_service import extract_text, save_file, validate_file
from app.api.services.parser import (
    extract_skills,
    extract_total_experience,
    extract_education,
)

# ✅ Embedding + Vector Search
from app.api.services.embedding_service import generate_embedding
from app.api.services.vector_store import search_similar


# =========================================================
# 1. JOB DESCRIPTION UPLOAD (FILE INPUT)
# =========================================================


# -------------------------
# FILE UPLOAD JOB DESCRIPTION
# -------------------------
async def process_job_description(file: UploadFile, db: AsyncSession):
    validate_file(file)

    file_path = await save_file(file)
    text = extract_text(file_path)

    # -------------------------
    # 1. EXTRACT FIRST
    # -------------------------
    skills = await extract_skills(text, db)
    experience = extract_total_experience(text)
    education = extract_education(text)

    # -------------------------
    # 2. EMBEDDING
    # -------------------------
    embedding = generate_embedding(text)

    # -------------------------
    # 3. DB WRITE LAST
    # -------------------------
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


# =========================================================
# 2. MANUAL JOB CREATION (JSON INPUT)
# =========================================================
async def create_job(data, db: AsyncSession):

    # -------------------------
    # 1. EXTRACT FIRST (NO DB)
    # -------------------------
    skills = await extract_skills(data.description_text, db)
    experience = extract_total_experience(data.description_text)
    education = extract_education(data.description_text)

    # -------------------------
    # 2. GENERATE EMBEDDING
    # -------------------------
    embedding = generate_embedding(data.description_text)

    # -------------------------
    # 3. ONLY THEN DB WRITE
    # -------------------------
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


# =========================================================
# 3. (OPTIONAL) MATCHING FUNCTION (READY FOR NEXT STEP)
# =========================================================
async def find_similar_candidates(job_description: str):
    """
    Future-ready: returns similar candidates using FAISS
    """
    embedding = generate_embedding(job_description)

    results = search_similar(embedding, top_k=5)

    return {"matches": results}
