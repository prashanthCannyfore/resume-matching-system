import faiss
import numpy as np
import pickle
import os
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

DIMENSION = 384
INDEX_FILE = "faiss_index.bin"
MAPPING_FILE = "faiss_mapping.pkl"

index = faiss.IndexFlatL2(DIMENSION)
id_mapping: Dict[int, int] = {}
vector_id = 0


def save_index():
    faiss.write_index(index, INDEX_FILE)
    with open(MAPPING_FILE, "wb") as f:
        pickle.dump((id_mapping, vector_id), f)


def load_index():
    global index, id_mapping, vector_id
    if os.path.exists(INDEX_FILE) and os.path.exists(MAPPING_FILE):
        index = faiss.read_index(INDEX_FILE)
        with open(MAPPING_FILE, "rb") as f:
            id_mapping, vector_id = pickle.load(f)
        print(f"FAISS loaded: {index.ntotal} vectors")
    else:
        print("No FAISS index found yet")


def normalize_vector(vec: List[float]):
    if not vec:
        return np.zeros(DIMENSION, dtype="float32")
    vec = np.array(vec).astype("float32")
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else vec


def add_embedding(candidate_id: int, embedding: List[float]):
    global vector_id
    vector = normalize_vector(embedding).reshape(1, -1)
    index.add(vector)
    id_mapping[vector_id] = candidate_id
    vector_id += 1
    save_index()


def search_similar(embedding: List[float], top_k: int = 5):
    if index.ntotal == 0:
        return []
    query = normalize_vector(embedding).reshape(1, -1)
    distances, indices = index.search(query, top_k)
    results = []
    for i, idx in enumerate(indices[0]):
        if idx in id_mapping:
            similarity = 1 / (1 + distances[0][i])
            results.append(
                {
                    "candidate_id": id_mapping[idx],
                    "similarity": round(float(similarity), 3),
                }
            )
    return results


async def rebuild_faiss_from_db(db: AsyncSession):
    """Rebuild entire FAISS index from PostgreSQL candidates"""
    global index, id_mapping, vector_id

    # Clear current index
    index = faiss.IndexFlatL2(DIMENSION)
    id_mapping = {}
    vector_id = 0

    from app.api.models.candidate import Candidate

    result = await db.execute(select(Candidate))
    candidates = result.scalars().all()

    for c in candidates:
        if c.embedding:
            try:
                embedding = (
                    json.loads(c.embedding)
                    if isinstance(c.embedding, str)
                    else c.embedding
                )
                add_embedding(c.id, embedding)
            except:
                pass  # skip corrupted embedding

    print(f"FAISS rebuilt with {index.ntotal} candidates")
    return {"rebuilt": True, "total_candidates": index.ntotal}


# Auto-load on import
import json

load_index()
