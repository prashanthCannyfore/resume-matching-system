"""
One-time fix: re-normalize skills for all candidates in the DB.

Run from backend directory:
    python fix_skills.py

What it does:
1. Loads every candidate's stored skills
2. Runs each skill through normalize_skill_name
3. Filters out sentence-length garbage entries (> 5 words)
4. Deduplicates
5. Saves back to DB
"""
import asyncio, sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:newpassword123@localhost:5432/resume_db"
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_EMBED_MODEL", "nomic-embed-text")
os.environ.setdefault("OLLAMA_LLM_MODEL", "llama3.2:3b")
os.environ.setdefault("OLLAMA_TIMEOUT", "90.0")
os.environ.setdefault("OLLAMA_CONTEXT_LENGTH", "2048")
os.environ.setdefault("OLLAMA_EMBED_CONCURRENCY", "2")

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("fix_skills")


def clean_skill_list(raw_skills: list[str]) -> list[str]:
    """
    Apply the full normalization + filtering pipeline to a stored skill list.
    """
    from app.api.services.parser import normalize_skill_name

    # Words that indicate a sentence/phrase, not a skill name
    _SENTENCE_INDICATORS = (
        "certification in", "certified", "experience in",
        "knowledge of", "proficient in", "expertise in",
        "hands-on", "skilled in", "cleared", "integrated",
        "summary", "strong knowledge", "development using",
        "front-end development", "back-end development",
        "experience with databases", "visualization using",
        "lightweight llms", "natural language",
        "and react with", "such as",
    )

    result = []
    seen = set()
    for skill in raw_skills:
        if not skill or not isinstance(skill, str):
            continue
        s = skill.strip()
        lower = s.lower()

        # Skip sentence-length entries (> 4 words)
        if len(s.split()) > 4:
            continue

        # Skip entries containing sentence indicators
        if any(ind in lower for ind in _SENTENCE_INDICATORS):
            continue

        # Skip entries starting with noise words
        if any(lower.startswith(p) for p in (
            "certification", "certified", "cleared", "integrated",
            "summary", "strong", "expertise", "and ", "or ",
        )):
            continue

        canonical = normalize_skill_name(s)
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


async def main():
    from app.core.database import AsyncSessionLocal, engine, Base
    from app.api.models.candidate import Candidate
    from sqlalchemy import select, update

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Candidate))
        candidates = r.scalars().all()
        log.info("Found %d candidates", len(candidates))

        for c in candidates:
            raw = c.skills or []
            cleaned = clean_skill_list(raw)

            # If cleaning left fewer than 3 skills AND we have resume text,
            # re-extract from the raw resume text using the full pipeline
            if len(cleaned) < 3 and c.resume_text:
                log.info("  RE-EXTRACT id=%-3d %s (only %d skills after clean)",
                         c.id, c.name[:40], len(cleaned))
                from app.api.services.parser import extract_skills
                re_extracted = await extract_skills(c.resume_text, db)
                if len(re_extracted) > len(cleaned):
                    cleaned = re_extracted
                    log.info("    re-extracted: %s", cleaned)

            if cleaned == raw:
                log.info("  SKIP  id=%-3d %s (no change)", c.id, c.name[:40])
                continue

            log.info("  FIX   id=%-3d %s", c.id, c.name[:40])
            log.info("    before: %s", raw)
            log.info("    after:  %s", cleaned)

            await db.execute(
                update(Candidate)
                .where(Candidate.id == c.id)
                .values(skills=cleaned)
            )

        await db.commit()
        log.info("Done — skills normalized for all candidates")


if __name__ == "__main__":
    asyncio.run(main())
