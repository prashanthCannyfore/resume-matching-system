"""
FAISS vector store — 768-dim (nomic-embed-text).

Key fixes vs previous version:
- add_embedding() now correctly handles re-uploads: removes the OLD vector
  from id_mapping before adding the new one, preventing orphaned entries.
- search_similar() logs candidate scores for debugging.
- rebuild_faiss_from_db() logs skipped candidates with reasons.
- Dimension guard on load discards stale 384-dim indexes cleanly.
"""
import faiss
import json
import logging
import os
import pickle
from typing import Dict, List

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models.candidate import Candidate

logger = logging.getLogger(__name__)

DIMENSION    = 768          # nomic-embed-text output dimension
INDEX_FILE   = "faiss_index.bin"
MAPPING_FILE = "faiss_mapping.pkl"

# Global state
index:               faiss.IndexFlatIP
id_mapping:          Dict[int, int]   # faiss_slot → candidate_id
candidate_to_vector: Dict[int, int]   # candidate_id → faiss_slot
vector_id:           int              # next available slot counter


def _reset_index() -> None:
    global index, id_mapping, candidate_to_vector, vector_id
    index               = faiss.IndexFlatIP(DIMENSION)
    id_mapping          = {}
    candidate_to_vector = {}
    vector_id           = 0


_reset_index()   # initialise globals


# ─── Persistence ──────────────────────────────────────────────────────────────
def save_index() -> None:
    faiss.write_index(index, INDEX_FILE)
    with open(MAPPING_FILE, "wb") as f:
        pickle.dump((id_mapping, candidate_to_vector, vector_id), f)
    logger.debug(f"[faiss] Saved index: {index.ntotal} vectors")


def load_index() -> None:
    global index, id_mapping, candidate_to_vector, vector_id
    try:
        if not (os.path.exists(INDEX_FILE) and os.path.exists(MAPPING_FILE)):
            logger.info("[faiss] No index files found — starting fresh")
            return

        loaded = faiss.read_index(INDEX_FILE)
        if loaded.d != DIMENSION:
            logger.warning(
                f"[faiss] Stale index dimension {loaded.d} (expected {DIMENSION}). "
                "Discarding. Call POST /api/vector/rebuild to regenerate."
            )
            _reset_index()
            return

        with open(MAPPING_FILE, "rb") as f:
            data = pickle.load(f)

        if len(data) == 3:
            id_mapping, candidate_to_vector, vector_id = data
        else:
            # Legacy 2-tuple format
            id_mapping, vector_id = data
            candidate_to_vector = {v: k for k, v in id_mapping.items()}

        index = loaded
        logger.info(
            f"[faiss] Loaded: {index.ntotal} vectors, "
            f"{len(candidate_to_vector)} candidates, dim={DIMENSION}"
        )

    except Exception as e:
        logger.error(f"[faiss] Load failed: {e} — starting fresh")
        _reset_index()


# ─── Vector math ──────────────────────────────────────────────────────────────
def normalize_vector(vec: List[float]) -> np.ndarray:
    """L2-normalise so IndexFlatIP gives cosine similarity."""
    arr = np.array(vec, dtype="float32")

    if len(arr) != DIMENSION:
        logger.warning(f"[faiss] Vector dim={len(arr)}, expected {DIMENSION} — padding/truncating")
        padded = np.zeros(DIMENSION, dtype="float32")
        padded[: min(len(arr), DIMENSION)] = arr[:DIMENSION]
        arr = padded

    norm = np.linalg.norm(arr)
    return arr / norm if norm > 1e-9 else arr


def _is_zero_vector(vec: List[float]) -> bool:
    return all(v == 0.0 for v in vec[:10])   # check first 10 elements


# ─── CRUD ─────────────────────────────────────────────────────────────────────
def add_embedding(candidate_id: int, embedding: List[float]) -> bool:
    """
    Add or update a candidate's embedding in the FAISS index.
    Returns True on success, False if the embedding is a zero vector (skip).

    Fix: when a candidate is re-uploaded, their old faiss_slot is removed from
    id_mapping so it no longer maps to any candidate_id. The new vector gets a
    fresh slot. This prevents the mapping corruption that caused 0 search results.
    """
    global vector_id

    if _is_zero_vector(embedding):
        logger.warning(f"[faiss] Skipping zero vector for candidate {candidate_id}")
        return False

    if len(embedding) != DIMENSION:
        logger.error(
            f"[faiss] candidate {candidate_id} embedding dim={len(embedding)}, "
            f"expected {DIMENSION}. Skipping."
        )
        return False

    # Remove stale mapping for this candidate (re-upload case)
    if candidate_id in candidate_to_vector:
        old_slot = candidate_to_vector[candidate_id]
        id_mapping.pop(old_slot, None)
        logger.debug(f"[faiss] Removed stale slot {old_slot} for candidate {candidate_id}")

    vec = normalize_vector(embedding).reshape(1, -1)
    index.add(vec)

    id_mapping[vector_id]          = candidate_id
    candidate_to_vector[candidate_id] = vector_id
    vector_id += 1

    save_index()
    logger.info(f"[faiss] Added candidate {candidate_id} at slot {vector_id-1}. Total={index.ntotal}")
    return True


def search_similar(embedding: List[float], top_k: int = 10) -> List[Dict]:
    """
    Return top-k candidates by cosine similarity.
    Skips zero vectors (failed embeddings) so they don't pollute results.
    """
    if index.ntotal == 0:
        logger.warning("[faiss] Index is empty — no candidates to search")
        return []

    if _is_zero_vector(embedding):
        logger.error("[faiss] Query is a zero vector — embedding generation failed")
        return []

    query  = normalize_vector(embedding).reshape(1, -1)
    k      = min(top_k, index.ntotal)
    scores, indices = index.search(query, k)

    results = []
    for i, slot in enumerate(indices[0]):
        if slot == -1:
            continue
        candidate_id = id_mapping.get(int(slot))
        if candidate_id is None:
            logger.debug(f"[faiss] Slot {slot} has no candidate mapping — orphaned vector, skipping")
            continue
        similarity = float(np.clip(scores[0][i], 0.0, 1.0))
        logger.debug(f"[faiss] candidate_id={candidate_id} slot={slot} similarity={similarity:.4f}")
        results.append({"candidate_id": candidate_id, "similarity": round(similarity, 4)})

    logger.info(f"[faiss] Search returned {len(results)} candidates (top_k={top_k}, index_size={index.ntotal})")
    return results


# ─── Rebuild ──────────────────────────────────────────────────────────────────
async def rebuild_faiss_from_db(db: AsyncSession) -> int:
    """Rebuild the entire FAISS index from embeddings stored in PostgreSQL."""
    _reset_index()

    result  = await db.execute(select(Candidate))
    all_candidates = result.scalars().all()

    rebuilt = skipped_null = skipped_dim = skipped_zero = 0

    for c in all_candidates:
        if not c.embedding:
            logger.debug(f"[faiss] Candidate {c.id} has no embedding — skipping")
            skipped_null += 1
            continue
        try:
            emb = json.loads(c.embedding) if isinstance(c.embedding, str) else c.embedding

            if len(emb) != DIMENSION:
                logger.warning(f"[faiss] Candidate {c.id} dim={len(emb)} != {DIMENSION} — skipping")
                skipped_dim += 1
                continue

            if _is_zero_vector(emb):
                logger.warning(f"[faiss] Candidate {c.id} has zero vector — skipping")
                skipped_zero += 1
                continue

            global vector_id
            vec = normalize_vector(emb).reshape(1, -1)
            index.add(vec)
            id_mapping[vector_id]          = c.id
            candidate_to_vector[c.id]      = vector_id
            vector_id += 1
            rebuilt += 1

        except Exception as e:
            logger.error(f"[faiss] Failed to rebuild candidate {c.id}: {e}")

    save_index()
    logger.info(
        f"[faiss] Rebuild complete: {rebuilt} added, "
        f"{skipped_null} no-embedding, {skipped_dim} wrong-dim, {skipped_zero} zero-vector"
    )
    return rebuilt


# Auto-load on import
load_index()
