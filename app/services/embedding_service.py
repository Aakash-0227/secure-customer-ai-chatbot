
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load and cache the embedding model."""
    return SentenceTransformer(MODEL_NAME)


def generate_embedding(text: str) -> list[float]:
    """Convert text into a normalized 384-dimensional vector."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    model = get_embedding_model()

    embedding = model.encode(
        text.strip(),
        normalize_embeddings=True,
    )

    return embedding.tolist()
