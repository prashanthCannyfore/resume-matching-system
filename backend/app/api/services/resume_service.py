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
from app.api.services.embedding_service import generate_embedding_async
from app.api.services.vector_store import add_embedding


async def process_resume(file: UploadFile, db: AsyncSession):
    # ── Validate + save ──────────────────────────────────────────────────────
    validate_file(file)
    file_path = await save_file(file)
    text = extract_text(file_path)

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    # ── Parse (all CPU-bound, run sequentially) ───────────────────────────────
    skills = await extract_skills(text, db)
    experience = extract_total_experience(text)
    education = extract_education(text)
    skill_exp = await extract_skill_experience(text, db)
    parsed_insight = await generate_resume_insight(text, db)
    email = extract_email(text)

    # ── Embedding (async Ollama call) ─────────────────────────────────────────
    embedding = await generate_embedding_async(text)

    # ── Upsert logic ──────────────────────────────────────────────────────────
    if email:
        result = await db.execute(select(Candidate).where(Candidate.email == email))
        existing = result.scalar_one_or_none()

        if existing:
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
                )
            )
            await db.commit()
            await db.refresh(existing)
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

    # ── Create new candidate ──────────────────────────────────────────────────
    candidate = Candidate(
        name=file.filename,
        email=email or f"noemail_{file.filename}_{hash(text[:100])}",
        skills=skills,
        experience_years=experience,
        education=education,
        resume_text=text,
        embedding=json.dumps(embedding),
    )

    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
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
