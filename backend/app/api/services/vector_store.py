import faiss
import numpy as np
import pickle
import os
import json
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.models.candidate import Candidate

DIMENSION = 384
INDEX_FILE = "faiss_index.bin"
MAPPING_FILE = "faiss_mapping.pkl"

index = faiss.IndexFlatL2(DIMENSION)
id_mapping: Dict[int, int] = {}
candidate_to_vector: Dict[int, int] = {}
vector_id = 0


def save_index():
    faiss.write_index(index, INDEX_FILE)
    with open(MAPPING_FILE, "wb") as f:
        pickle.dump((id_mapping, candidate_to_vector, vector_id), f)


def load_index():
    global index, id_mapping, candidate_to_vector, vector_id
    try:
        if os.path.exists(INDEX_FILE) and os.path.exists(MAPPING_FILE):
            index = faiss.read_index(INDEX_FILE)
            with open(MAPPING_FILE, "rb") as f:
                data = pickle.load(f)
                if len(data) == 3:
                    id_mapping, candidate_to_vector, vector_id = data
                else:
                    # Old format compatibility
                    id_mapping, vector_id = data
                    candidate_to_vector = {}
            print(f"FAISS loaded: {index.ntotal} vectors")
        else:
            print("No FAISS index found, starting fresh")
    except Exception as e:
        print(f"Error loading FAISS: {e}. Starting fresh.")
        index = faiss.IndexFlatL2(DIMENSION)
        id_mapping = {}
        candidate_to_vector = {}
        vector_id = 0


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
    candidate_to_vector[candidate_id] = vector_id
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
            results.append({
                "candidate_id": id_mapping[idx],
                "similarity": round(float(similarity), 3),
            })
    return results


async def rebuild_faiss_from_db(db: AsyncSession):
    global index, id_mapping, candidate_to_vector, vector_id
    index = faiss.IndexFlatL2(DIMENSION)
    id_mapping = {}
    candidate_to_vector = {}
    vector_id = 0

    result = await db.execute(select(Candidate))
    for c in result.scalars().all():
        if c.embedding:
            try:
                emb = json.loads(c.embedding) if isinstance(c.embedding, str) else c.embedding
                vector = normalize_vector(emb).reshape(1, -1)
                index.add(vector)
                id_mapping[vector_id] = c.id
                candidate_to_vector[c.id] = vector_id
                vector_id += 1
            except:
                pass

    save_index()
    print(f"FAISS rebuilt with {index.ntotal} candidates")


# Auto-load
load_index()