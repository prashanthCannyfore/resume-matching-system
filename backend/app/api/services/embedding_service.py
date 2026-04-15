from sentence_transformers import SentenceTransformer

# Load model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(text: str) -> list:
    if not text:
        return []

    return model.encode(text).tolist()