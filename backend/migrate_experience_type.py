#!/usr/bin/env python3
"""
Migration script:
1. Alters experience_years column from INTEGER to FLOAT (double precision)
2. Re-parses all existing candidates to update their experience_years with month-level precision
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal
from app.api.services.parser import extract_total_experience


async def migrate():
    print("=== Migration: experience_years → FLOAT + re-parse ===\n")

    async with engine.begin() as conn:
        # 1. Check current column type
        result = await conn.execute(text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name='candidates' AND column_name='experience_years'
        """))
        row = result.fetchone()
        current_type = row[0] if row else "unknown"
        print(f"Current column type: {current_type}")

        # 2. Alter if not already float
        if current_type not in ("double precision", "real", "numeric"):
            print("Altering column to double precision...")
            await conn.execute(text("""
                ALTER TABLE candidates
                ALTER COLUMN experience_years TYPE double precision
                USING experience_years::double precision
            """))
            print("✓ Column altered to double precision")
        else:
            print("✓ Column already float — skipping ALTER")

    # 3. Re-parse all candidates and update experience_years
    print("\nRe-parsing experience for all candidates...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id, resume_text, experience_years FROM candidates"))
        rows = result.fetchall()
        print(f"Found {len(rows)} candidate(s)\n")

        updated = 0
        for row in rows:
            cid, resume_text, old_exp = row
            if not resume_text:
                print(f"  Candidate {cid}: no resume text, skipping")
                continue

            new_exp = extract_total_experience(resume_text)
            print(f"  Candidate {cid}: {old_exp} → {new_exp} years")

            await session.execute(
                text("UPDATE candidates SET experience_years = :exp WHERE id = :id"),
                {"exp": new_exp, "id": cid}
            )
            updated += 1

        await session.commit()
        print(f"\n✓ Updated {updated} candidate(s)")

    print("\n=== Migration complete ===")


if __name__ == "__main__":
    asyncio.run(migrate())
