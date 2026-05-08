from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import json

from app.api.models.candidate import Candidate
from app.api.services.file_service import validate_file, save_file, extract_text
from app.api.services.parser import (
    extract_skills,
    extract_total_experience,
    extract_education,
    extract_skill_experience,
    extract_email,
    generate_resume_insight,
)
from app.api.services.embedding_service import generate_embedding
from app.api.services.vector_store import add_embedding


async def process_resume(file: UploadFile, db: AsyncSession):
    # ------------------------- VALIDATE + SAVE -------------------------
    validate_file(file)
    file_path = await save_file(file)
    text = extract_text(file_path)

    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    # ------------------------- PARSING -------------------------
    skills = await extract_skills(text, db)
    experience = extract_total_experience(text)
    education = extract_education(text)
    skill_exp = await extract_skill_experience(text, db)
    parsed_insight = await generate_resume_insight(text, db)
    email = extract_email(text)

    # ------------------------- EMBEDDING -------------------------
    embedding = generate_embedding(text)

    # ------------------------- HANDLE EXISTING CANDIDATE -------------------------
    if email:
        # Check if candidate with this email already exists
        result = await db.execute(select(Candidate).where(Candidate.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing candidate instead of creating duplicate
            await db.execute(
                update(Candidate)
                .where(Candidate.id == existing.id)
                .values(
                    name=file.filename,
                    skills=skills,
                    experience_years=experience,
                    education=education,
                    resume_text=text,
                    embedding=json.dumps(embedding),
                    # You can add more fields here if needed
                )
            )
            await db.commit()
            await db.refresh(existing)

            # Update vector store
            add_embedding(existing.id, embedding)

            return {
                "id": existing.id,
                "message": "Candidate updated successfully (email already existed)",
                "skills": skills,
                "experience": experience,
                "education": education,
                "skill_experience": skill_exp,
                "parsed_insight": parsed_insight,
            }

    # ------------------------- CREATE NEW CANDIDATE -------------------------
    candidate = Candidate(
        name=file.filename,
        email=email
        or f"noemail_{file.filename}_{hash(text[:100])}",  # fallback unique email
        skills=skills,
        experience_years=experience,
        education=education,
        resume_text=text,
        embedding=json.dumps(embedding),
    )

    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    # Add to FAISS vector store
    add_embedding(candidate.id, embedding)

    return {
        "id": candidate.id,
        "message": "Candidate created successfully",
        "skills": skills,
        "experience": experience,
        "education": education,
        "skill_experience": skill_exp,
        "parsed_insight": parsed_insight,
    }
