
"""add knowledge chunks table

Revision ID: 1e3cf6a1d7ff
Revises: fa0deb2d5794
Create Date: 2026-10-22 19:39:24.458957
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR


# Revision identifiers used by Alembic.
revision: str = "1e3cf6a1d7ff"
down_revision: Union[str, Sequence[str], None] = "fa0deb2d5794"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the knowledge chunks table."""

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("embedding", VECTOR(384), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_knowledge_chunks_customer_id",
        "knowledge_chunks",
        ["customer_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the knowledge chunks table."""

    op.drop_index(
        "ix_knowledge_chunks_customer_id",
        table_name="knowledge_chunks",
    )
    op.drop_table("knowledge_chunks")
