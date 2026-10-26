
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import Invoice
from app.schemas import InvoiceCreate
from app.services.auth_dependency import get_current_customer_id
from app.services.invoice_service import index_customer_invoice


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_invoices(
    status: str | None = None,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    """List invoices belonging only to the authenticated customer."""

    query = db.query(Invoice).filter(
        Invoice.customer_id == customer_id
    )

    if status:
        query = query.filter(Invoice.status.ilike(status.strip()))

    return query.order_by(Invoice.id.asc()).all()


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    """Return an invoice only if it belongs to the authenticated customer."""

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id,
            Invoice.customer_id == customer_id,
        )
        .first()
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    return invoice


@router.post("/", status_code=201)
def create_invoice(
    payload: InvoiceCreate,
    customer_id: int = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    """Create an invoice for the authenticated customer."""

    invoice_number = payload.invoice_number.strip()

    if not invoice_number:
        raise HTTPException(
            status_code=422,
            detail="Invoice number cannot be empty.",
        )

    # Prevent duplicates for the authenticated customer.
    existing = (
        db.query(Invoice)
        .filter(
            Invoice.customer_id == customer_id,
            Invoice.invoice_number == invoice_number,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An invoice with this number already exists.",
        )

    invoice = Invoice(
        customer_id=customer_id,
        invoice_number=invoice_number,
        invoice_date=payload.invoice_date,
        amount=payload.amount,
        currency=payload.currency.upper(),
        status=payload.status.lower(),
    )

    try:
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An invoice with this number already exists.",
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Invoice could not be created.",
        )

    # PostgreSQL is the source of truth.
    # Indexing errors must not imply that the invoice was lost.
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
        # The invoice was committed before indexing began.
        # A separate retry/reindex operation is still needed.

    return {
        "id": invoice.id,
        "customer_id": invoice.customer_id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.isoformat(),
        "amount": str(invoice.amount),
        "currency": invoice.currency,
        "status": invoice.status,
        "indexing_status": indexing_status,
    }
