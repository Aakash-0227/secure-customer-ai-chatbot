
from app.models import Customer, Invoice, Conversation, Message
from app.database import SessionLocal
from app.services.invoice_service import (
    get_customer_invoices,
    index_customer_invoice,
)
from app.services.knowledge_service import search_knowledge


def main():
    db = SessionLocal()

    try:
        # Find an existing invoice belonging to customer ID 1.
        invoice = (
            db.query(Invoice)
            .filter(Invoice.customer_id == 1)
            .first()
        )

        if invoice is None:
            print("No invoice found for customer ID 1.")
            return

        print("Invoice selected:", invoice.invoice_number)

        # Index this invoice in the vector knowledge store.
        result = index_customer_invoice(
            db=db,
            customer_id=1,
            invoice_id=invoice.id,
        )
        print("Indexing result:", result)

        # Search only customer ID 1's knowledge.
        results = search_knowledge(
            db=db,
            customer_id=1,
            query=f"Tell me about invoice {invoice.invoice_number}",
            limit=5,
        )

        print("\nSearch results:")
        for item in results:
            print(f"ID: {item.id}")
            print(f"Content: {item.content}")
            print(f"Source type: {item.source_type}")
            print(f"Source ID: {item.source_id}")
            print("-" * 40)

    except Exception as error:
        db.rollback()
        print("Test failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()
