from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.api.models.candidate import Candidate
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

# ✅ NEW (Embedding + Vector DB)
from app.api.services.embedding_service import generate_embedding
from app.api.services.vector_store import add_embedding


# -------------------------
# RESUME PROCESSING
# -------------------------
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
    # -------- NLP EXTRACTION --------
    skills = await extract_skills(text, db)
    experience = extract_total_experience(text)
    education = extract_education(text)
    skill_exp = await extract_skill_experience(text, db)
    email = extract_email(text)

    # -------- EMBEDDING --------
    embedding = generate_embedding(text)

    # -------- DB SAVE --------
    # fallback email
    if not email:
        email = f""

    # -------------------------
    # SAVE TO DB
    # -------------------------
    candidate = Candidate(
        name=file.filename,   # later improve via NLP
        email=email,
        skills=skills,
        experience_years=experience,
        education=education,
        resume_text=text,
        embedding=json.dumps(embedding)   # ✅ store vector as JSON
    )

    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    # -------- VECTOR STORE (FAISS) --------
    add_embedding(candidate.id, embedding)

    # -------- RESPONSE --------
    return {
        "id": candidate.id,
        "skills": skills,
        "experience": experience,
        "education": education,
        "skill_experience": skill_exp
    }