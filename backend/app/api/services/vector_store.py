import faiss
import numpy as np
from typing import List, Dict

DIMENSION = 384

index = faiss.IndexFlatL2(DIMENSION)

id_mapping: Dict[int, int] = {}
vector_id = 0


def normalize_vector(vec: List[float]):
    if not vec:
        return np.zeros(DIMENSION, dtype="float32")

    vec = np.array(vec).astype("float32")
    norm = np.linalg.norm(vec)

    if norm == 0:
        return vec

    return vec / norm


def add_embedding(candidate_id: int, embedding: List[float]):
    global vector_id

    vector = normalize_vector(embedding).reshape(1, -1)

    index.add(vector)
    id_mapping[vector_id] = candidate_id
    vector_id += 1


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
