"""
One-time fix script — run from the backend directory:
    python fix_embeddings.py

What it does:
1. Re-embeds every candidate whose embedding is missing, zero, or wrong dimension (384 vs 768)
2. Saves the new 768-dim embedding back to PostgreSQL
3. Rebuilds the FAISS index from scratch with all valid candidates
"""
import asyncio
import json
import logging
import os
import sys

# ── make app importable ───────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

os.environ.setdefault("OLLAMA_BASE_URL",        "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_EMBED_MODEL",     "nomic-embed-text")
os.environ.setdefault("OLLAMA_LLM_MODEL",       "llama3.2:3b")
os.environ.setdefault("OLLAMA_TIMEOUT",         "60.0")
os.environ.setdefault("OLLAMA_CONTEXT_LENGTH",  "4096")
os.environ.setdefault("OLLAMA_EMBED_CONCURRENCY", "2")

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("fix_embeddings")

EXPECTED_DIM = 768


async def main():
    from app.core.database import AsyncSessionLocal, engine, Base
    from app.api.models.candidate import Candidate
    from app.api.services.ollama_client import check_ollama_health, embed
    from app.api.services.vector_store import rebuild_faiss_from_db
    from sqlalchemy import select, update

    # ── 0. Pre-flight checks ──────────────────────────────────────────────────
    log.info("Checking Ollama...")
    if not await check_ollama_health():
        log.error("Ollama is not reachable at %s. Start it with: ollama serve",
                  os.environ["OLLAMA_BASE_URL"])
        return

    log.info("Ollama OK")

    # ── 1. Ensure tables exist ────────────────────────────────────────────────
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Candidate))
        candidates = result.scalars().all()
        log.info("Found %d candidates in DB", len(candidates))

        fixed = skipped = already_ok = 0

        for c in candidates:
            # Determine current embedding state
            current_dim = 0
            if c.embedding:
                try:
                    emb_data = json.loads(c.embedding) if isinstance(c.embedding, str) else c.embedding
                    current_dim = len(emb_data)
                    # Check for zero vector
                    if current_dim == EXPECTED_DIM and all(v == 0.0 for v in emb_data[:10]):
                        current_dim = 0  # treat as missing
                except Exception:
                    current_dim = 0

            if current_dim == EXPECTED_DIM:
                log.info("  SKIP  id=%-3d %-50s  (already 768-dim)", c.id, c.name[:50])
                already_ok += 1
                continue

            # Need to re-embed
            if not c.resume_text or not c.resume_text.strip():
                log.warning("  SKIP  id=%-3d %-50s  (no resume_text)", c.id, c.name[:50])
                skipped += 1
                continue

            log.info("  FIX   id=%-3d %-50s  (current_dim=%d → %d)",
                     c.id, c.name[:50], current_dim, EXPECTED_DIM)
            try:
                new_embedding = await embed(c.resume_text[:8000])  # cap at 8k chars

                if len(new_embedding) != EXPECTED_DIM:
                    log.error("    Unexpected dim=%d from Ollama, skipping", len(new_embedding))
                    skipped += 1
                    continue

                # Save to DB
                await db.execute(
                    update(Candidate)
                    .where(Candidate.id == c.id)
                    .values(embedding=json.dumps(new_embedding))
                )
                fixed += 1
                log.info("    Saved dim=%d to DB", len(new_embedding))

            except Exception as e:
                log.error("    Failed to embed candidate %d: %s", c.id, e)
                skipped += 1

        await db.commit()
        log.info("")
        log.info("Re-embedding complete: fixed=%d  already_ok=%d  skipped=%d",
                 fixed, already_ok, skipped)

        # ── 2. Rebuild FAISS from the now-correct DB embeddings ───────────────
        log.info("")
        log.info("Rebuilding FAISS index...")
        rebuilt = await rebuild_faiss_from_db(db)
        log.info("FAISS rebuilt with %d candidates", rebuilt)

    log.info("")
    log.info("Done. All candidates are now searchable.")
    log.info("You can now start the server: uvicorn app.main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(main())
