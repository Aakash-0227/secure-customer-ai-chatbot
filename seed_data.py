
from datetime import datetime, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models import Customer, Invoice


def seed_data():
    db = SessionLocal()

    try:
        customers_data = [
            {
                "name": "Arun",
                "email": "arun@example.com",
                "phone": "9876543210",
            },
            {
                "name": "Deepa",
                "email": "deepa@example.com",
                "phone": "9123456780",
            },
        ]

        for data in customers_data:
            customer = (
                db.query(Customer)
                .filter(Customer.phone == data["phone"])
                .first()
            )

            if customer is None:
                customer = Customer(**data)
                db.add(customer)
                db.flush()

            invoices_data = [
                {
                    "invoice_number": f"INV-{300 + i}",
                    "invoice_date": datetime(
                        2026, 10, 22, tzinfo=timezone.utc
                    ),
                    "amount": Decimal("1250.00") if i == 0
                    else Decimal(str(500 + i * 250)),
                    "status": "unpaid" if i % 2 == 0 else "paid",
                }
                for i in range(5)
            ]

            for invoice_data in invoices_data:
                existing = (
                    db.query(Invoice)
                    .filter(
                        Invoice.customer_id == customer.id,
                        Invoice.invoice_number
                        == invoice_data["invoice_number"],
                    )
                    .first()
                )

                if existing is None:
                    db.add(
                        Invoice(
                            customer_id=customer.id,
                            **invoice_data,
                        )
                    )
                    print(
                        f"Added {invoice_data['invoice_number']} "
                        f"for {customer.name}"
                    )

        db.commit()
        print("Customer and invoice seeding completed!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
