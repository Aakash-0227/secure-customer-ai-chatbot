
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=50)
    invoice_date: date
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    status: str = Field(default="unpaid", pattern="^(unpaid|paid)$")
