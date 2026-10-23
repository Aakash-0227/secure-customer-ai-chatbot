
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Invoice
from app.services.auth_dependency import get_current_customer_id


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
        query = query.filter(Invoice.status.ilike(status))

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
