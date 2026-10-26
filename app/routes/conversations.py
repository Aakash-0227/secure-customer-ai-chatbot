
import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import Conversation, Message, Customer, Invoice
from app.services.auth_dependency import get_current_customer_id
from app.services.llm_service import generate_response
from app.services.invoice_service import index_customer_invoice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])

# In-memory confirmation state for this running development server.
# Pending requests expire on server restart; invoices are stored in PostgreSQL.
pending_invoices = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=200)


class ChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


def get_owned_conversation(db: Session, conversation_id: int, customer_id: int):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.customer_id == customer_id,
        )
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


def save_message(db, conversation_id, role, content):
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def create_invoice_for_customer(db, customer_id, details):
    existing = (
        db.query(Invoice)
        .filter(
            Invoice.customer_id == customer_id,
            Invoice.invoice_number == details["invoice_number"],
        )
        .first()
    )
    if existing:
        return None, "An invoice with this number already exists."

    invoice = Invoice(
        customer_id=customer_id,
        invoice_number=details["invoice_number"],
        invoice_date=date.fromisoformat(details["invoice_date"]),
        amount=Decimal(str(details["amount"])),
        currency=details["currency"],
        status=details["status"],
    )

    try:
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
    except IntegrityError:
        db.rollback()
        return None, "An invoice with this number already exists."
    except Exception:
        db.rollback()
        logger.exception("Invoice creation failed")
        return None, "Invoice creation failed. Please try again."

    indexing_status = "pending"
    try:
        index_customer_invoice(
            db=db,
            customer_id=customer_id,
            invoice_id=invoice.id,
        )
        indexing_status = "indexed"
    except Exception:
        db.rollback()
        logger.exception("Invoice saved but vector indexing failed")

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.isoformat(),
        "amount": str(invoice.amount),
        "currency": invoice.currency,
        "status": invoice.status,
        "indexing_status": indexing_status,
    }, None


@router.post("/")
def create_conversation(
    payload: ConversationCreate,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    conversation = Conversation(
        customer_id=customer_id,
        title=payload.title.strip(),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
    }


@router.get("/")
def list_conversations(
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.customer_id == customer_id)
        .order_by(Conversation.id.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
        }
        for c in conversations
    ]


@router.get("/{conversation_id}/messages")
def list_messages(
    conversation_id: int,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    conversation = get_owned_conversation(db, conversation_id, customer_id)
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in messages
    ]


@router.post("/{conversation_id}/chat")
def chat(
    conversation_id: int,
    payload: ChatRequest,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    conversation = get_owned_conversation(db, conversation_id, customer_id)
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found.")

    prompt = payload.content.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    # Store the incoming user message.
    save_message(db, conversation.id, "user", prompt)
    key = (customer_id, conversation.id)
    normalized = prompt.lower().strip()

    # Confirm or cancel a previously proposed invoice.
    if key in pending_invoices and normalized in {
        "yes", "confirm", "confirmed", "yes confirm", "confirm invoice"
    }:
        details = pending_invoices.pop(key)
        invoice, error = create_invoice_for_customer(db, customer_id, details)
        if error:
            answer = error
            status = "rejected" if "already exists" in error else "failed"
        else:
            answer = (
                f"Invoice {invoice['invoice_number']} was created successfully. "
                f"Amount: {invoice['currency']} {invoice['amount']}; "
                f"status: {invoice['status']}; "
                f"vector indexing: {invoice['indexing_status']}."
            )
            status = "created"

        save_message(db, conversation.id, "assistant", answer)
        return {
            "conversation_id": conversation.id,
            "assistant_response": answer,
            "invoice_action": status,
            "invoice": invoice if not error else None,
            "invoice_records_used": 0,
            "knowledge_chunks_used": 0,
            "knowledge_sources": [],
        }

    if key in pending_invoices and normalized in {"no", "cancel", "don't create", "do not create"}:
        pending_invoices.pop(key, None)
        answer = "Invoice creation cancelled. No invoice was created."
        save_message(db, conversation.id, "assistant", answer)
        return {
            "conversation_id": conversation.id,
            "assistant_response": answer,
            "invoice_action": "cancelled",
            "invoice_records_used": 0,
            "knowledge_chunks_used": 0,
            "knowledge_sources": [],
        }

    # Detect an explicit invoice creation request and require all fields.
    create_request = any(
        phrase in normalized
        for phrase in ("create invoice", "add invoice", "make invoice")
    )
    if create_request:
        number_match = re.search(r"\bINV-[A-Z0-9-]+\b", prompt, re.I)
        date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", prompt)
        amount_match = re.search(
            r"(?:INR|₹|rs\.?)\s*([\d,]+(?:\.\d{1,2})?)|"
            r"\bamount\s*[:=]?\s*([\d,]+(?:\.\d{1,2})?)",
            prompt,
            re.I,
        )
        status_match = re.search(r"\b(unpaid|paid)\b", prompt, re.I)

        if not (number_match and date_match and amount_match and status_match):
            answer = (
                "Please provide the invoice number, date (YYYY-MM-DD), "
                "amount, currency (INR), and payment status (paid or unpaid)."
            )
        else:
            invoice_number = number_match.group(0).upper()
            existing = (
                db.query(Invoice)
                .filter(
                    Invoice.customer_id == customer_id,
                    Invoice.invoice_number == invoice_number,
                )
                .first()
            )
            if existing:
                answer = (
                    f"Invoice {invoice_number} already exists in your account. "
                    "I cannot create a duplicate."
                )
            else:
                try:
                    amount_text = (
                        amount_match.group(1) or amount_match.group(2)
                    ).replace(",", "")
                    amount = Decimal(amount_text)
                    invoice_date = date.fromisoformat(date_match.group(0))
                    if amount <= 0:
                        raise ValueError("Amount must be positive.")
                except (InvalidOperation, ValueError):
                    answer = "Please provide a valid date and positive amount."
                else:
                    details = {
                        "invoice_number": invoice_number,
                        "invoice_date": invoice_date.isoformat(),
                        "amount": str(amount),
                        "currency": "INR",
                        "status": status_match.group(1).lower(),
                    }
                    pending_invoices[key] = details
                    answer = (
                        f"Please confirm: create invoice {invoice_number} "
                        f"dated {details['invoice_date']} for INR {amount:.2f}, "
                        f"status {details['status']}? Reply 'confirm' to create "
                        "it or 'cancel' to discard the request."
                    )

        save_message(db, conversation.id, "assistant", answer)
        return {
            "conversation_id": conversation.id,
            "assistant_response": answer,
            "invoice_action": "pending_confirmation" if key in pending_invoices else "not_created",
            "invoice_records_used": 0,
            "knowledge_chunks_used": 0,
            "knowledge_sources": [],
        }

    # Ordinary messages (including greetings) do not create invoices.
    previous_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.asc())
        .all()
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in previous_messages[:-1]
        if m.role in {"user", "assistant"}
    ]

    try:
        answer = generate_response(
            db=db,
            customer_id=customer_id,
            user_message=prompt,
            customer_name=customer.name,
            chat_history=history,
        )
    except RuntimeError as exc:
        logger.exception("Chat generation failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected chat error")
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable.",
        ) from exc

    save_message(db, conversation.id, "assistant", answer)

    try:
        from app.services.knowledge_service import search_knowledge
        results = search_knowledge(
            db=db,
            customer_id=customer_id,
            query=prompt,
            limit=5,
        )
        sources = [
            {
                "id": item.id,
                "source_type": item.source_type,
                "source_id": item.source_id,
            }
            for item in results
        ]
    except Exception:
        logger.exception("Knowledge metadata lookup failed")
        sources = []

    return {
        "conversation_id": conversation.id,
        "user_message": prompt,
        "assistant_response": answer,
        "invoice_records_used": 0,
        "knowledge_chunks_used": len(sources),
        "knowledge_sources": sources,
    }
