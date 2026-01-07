from sentence_transformers import SentenceTransformer

# load once (important)
model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(text: str) -> list[float]:
    embedding = model.encode(text)
    return embedding.tolist()
