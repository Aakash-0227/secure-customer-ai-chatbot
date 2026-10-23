
from sqlalchemy.orm import Session

from app.models import Invoice
from app.models_knowledge import KnowledgeChunk
from app.services.knowledge_service import save_knowledge
from app.services.embedding_service import generate_embedding


def get_customer_invoices(
    db: Session,
    customer_id: int,
    status: str | None = None,
) -> list[dict]:
    """Retrieve invoices belonging only to the authenticated customer."""

    query = db.query(Invoice).filter(
        Invoice.customer_id == customer_id
    )

    if status:
        query = query.filter(
            Invoice.status.ilike(status.strip())
        )

    invoices = query.order_by(
        Invoice.invoice_date.desc()
    ).all()

    return [
        {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "amount": str(invoice.amount),
            "status": invoice.status,
        }
        for invoice in invoices
    ]


def get_customer_invoice_by_number(
    db: Session,
    customer_id: int,
    invoice_number: str,
) -> dict | None:
    """Find an invoice within the authenticated customer's records."""

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.customer_id == customer_id,
            Invoice.invoice_number == invoice_number.strip(),
        )
        .first()
    )

    if invoice is None:
        return None

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.isoformat(),
        "amount": str(invoice.amount),
        "status": invoice.status,
    }


def index_customer_invoice(
    db: Session,
    customer_id: int,
    invoice_id: int,
) -> dict:
    """Index an invoice for its owner, updating existing knowledge if needed."""

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id,
            Invoice.customer_id == customer_id,
        )
        .first()
    )

    if invoice is None:
        raise ValueError("Invoice not found for this customer.")

    content = (
        f"Invoice number: {invoice.invoice_number}. "
        f"Invoice date: {invoice.invoice_date.isoformat()}. "
        f"Amount: INR {invoice.amount}. "
        f"Payment status: {invoice.status}."
    )

    existing = (
        db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.customer_id == customer_id,
            KnowledgeChunk.source_type == "invoice",
            KnowledgeChunk.source_id == invoice.id,
        )
        .first()
    )

    if existing:
        existing.content = content
        existing.embedding = generate_embedding(content)
        db.commit()
        db.refresh(existing)

        return {
            "message": "Invoice knowledge updated.",
            "chunk_id": existing.id,
        }

    chunk = save_knowledge(
        db=db,
        customer_id=customer_id,
        content=content,
        source_type="invoice",
        source_id=invoice.id,
    )

    return {
        "message": "Invoice indexed successfully.",
        "chunk_id": chunk.id,
    }
