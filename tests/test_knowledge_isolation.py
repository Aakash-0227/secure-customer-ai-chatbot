
from app.database import SessionLocal
from app.services.knowledge_service import search_knowledge


def test_knowledge_search_isolated_by_customer():
    db = SessionLocal()

    try:
        # Arun's existing knowledge chunks should be available to Arun.
        arun_chunks = search_knowledge(
            db=db,
            customer_id=1,
            query="invoice INV-300",
        )

        # Deepa must not retrieve Arun's chunks.
        deepa_chunks = search_knowledge(
            db=db,
            customer_id=2,
            query="invoice INV-300",
        )

        assert all(
            chunk.customer_id == 1
            for chunk in arun_chunks
        )

        assert all(
            chunk.customer_id == 2
            for chunk in deepa_chunks
        )

        arun_chunk_ids = {chunk.id for chunk in arun_chunks}

        assert not any(
            chunk.id in arun_chunk_ids
            for chunk in deepa_chunks
        )

    finally:
        db.close()
