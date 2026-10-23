from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoices = relationship("Invoice", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint(
            "customer_id", "invoice_number",
            name="uq_customer_invoice_number",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False, default="unpaid")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="invoices")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False, index=True
    )
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("conversations.id"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")