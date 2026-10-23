
from app.database import SessionLocal
from app.services.knowledge_service import save_knowledge, search_knowledge
from app.models import Customer, Invoice, Conversation, Message

def main():
    db = SessionLocal()

    try:
        # Test data for customer ID 1
        chunk = save_knowledge(
            db=db,
            customer_id=1,
            content="Invoice INV-300 has an amount of INR 1250 and is currently unpaid.",
            source_type="test",
            source_id=None,
        )

        print("Knowledge saved successfully.")
        print("Chunk ID:", chunk.id)

        results = search_knowledge(
            db=db,
            customer_id=1,
            query="Which invoice is unpaid?",
            limit=3,
        )

        print("\nSearch results:")
        for result in results:
            print(f"ID: {result.id}")
            print(f"Content: {result.content}")
            print(f"Source: {result.source_type}")
            print("-" * 40)

    except Exception as error:
        db.rollback()
        print("Test failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()
