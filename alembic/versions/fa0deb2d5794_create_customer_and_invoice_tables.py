
"""create customer and invoice tables

Revision ID: fa0deb2d5794
Revises:
Create Date: 2026-10-22 15:01:09.887272
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Revision identifiers
revision: str = "fa0deb2d5794"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the new database tables."""

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_conversations_customer_id"),
        "conversations",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversations_id"),
        "conversations",
        ["id"],
        unique=False,
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(length=50), nullable=False),
        sa.Column("invoice_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_id",
            "invoice_number",
            name="uq_customer_invoice_number",
        ),
    )

    op.create_index(
        op.f("ix_invoices_customer_id"),
        "invoices",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_invoices_id"),
        "invoices",
        ["id"],
        unique=False,
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_messages_conversation_id"),
        "messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messages_id"),
        "messages",
        ["id"],
        unique=False,
    )

    # Remove the temporary starter table.
    op.drop_index(
        op.f("ix_chat_messages_id"),
        table_name="chat_messages",
    )
    op.drop_table("chat_messages")

    # Make customer phone mandatory.
    op.alter_column(
        "customers",
        "phone",
        existing_type=sa.VARCHAR(length=20),
        nullable=False,
    )

    # Give the phone uniqueness constraint an explicit name.
    op.create_unique_constraint(
        "uq_customers_phone",
        "customers",
        ["phone"],
    )


def downgrade() -> None:
    """Reverse the migration."""

    op.drop_constraint(
        "uq_customers_phone",
        "customers",
        type_="unique",
    )

    op.alter_column(
        "customers",
        "phone",
        existing_type=sa.VARCHAR(length=20),
        nullable=True,
    )

    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            sa.INTEGER(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.INTEGER(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "message",
            sa.TEXT(),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "response",
            sa.TEXT(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("chat_messages_pkey"),
        ),
    )

    op.create_index(
        op.f("ix_chat_messages_id"),
        "chat_messages",
        ["id"],
        unique=False,
    )

    op.drop_index(
        op.f("ix_messages_id"),
        table_name="messages",
    )
    op.drop_index(
        op.f("ix_messages_conversation_id"),
        table_name="messages",
    )
    op.drop_table("messages")

    op.drop_index(
        op.f("ix_invoices_id"),
        table_name="invoices",
    )
    op.drop_index(
        op.f("ix_invoices_customer_id"),
        table_name="invoices",
    )
    op.drop_table("invoices")

    op.drop_index(
        op.f("ix_conversations_id"),
        table_name="conversations",
    )
    op.drop_index(
        op.f("ix_conversations_customer_id"),
        table_name="conversations",
    )
    op.drop_table("conversations")
