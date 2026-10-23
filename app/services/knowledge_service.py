
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models_knowledge import KnowledgeChunk
from app.services.embedding_service import generate_embedding


def save_knowledge(
    db: Session,
    customer_id: int,
    content: str,
    source_type: str,
    source_id: int | None = None,
) -> KnowledgeChunk:
    """Save a knowledge chunk for a specific customer."""

    if not content or not content.strip():
        raise ValueError("Content cannot be empty.")

    embedding = generate_embedding(content.strip())

    chunk = KnowledgeChunk(
        customer_id=customer_id,
        content=content.strip(),
        source_type=source_type,
        source_id=source_id,
        embedding=embedding,
    )

    try:
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk
    except Exception:
        db.rollback()
        raise


def search_knowledge(
    db: Session,
    customer_id: int,
    query: str,
    limit: int = 5,
) -> list[KnowledgeChunk]:
    """Search only knowledge chunks belonging to the specified customer."""

    if not query or not query.strip():
        return []

    limit = max(1, min(limit, 10))
    query_embedding = generate_embedding(query.strip())

    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)

    statement = (
        select(KnowledgeChunk)
        .where(KnowledgeChunk.customer_id == customer_id)
        .order_by(distance)
        .limit(limit)
    )

    return list(db.scalars(statement).all())
