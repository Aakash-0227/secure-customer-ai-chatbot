
from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    text,
)
from pgvector.sqlalchemy import VECTOR

from app.database import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content = Column(Text, nullable=False)
    source_type = Column(Text, nullable=False)
    source_id = Column(Integer, nullable=True)

    embedding = Column(VECTOR(384), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
