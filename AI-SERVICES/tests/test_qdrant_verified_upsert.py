import pytest
import asyncio
from rag.chunker import document_chunker
from rag.qdrant_client import qdrant_service

def test_chunking_and_verified_upsert():
    async def _run():
        text = (
            "# Centrifugal Pump Maintenance Manual\n\n"
            "## Section 1: Mechanical Seals\n"
            "Mechanical seals must be inspected every 500 operating hours. "
            "Permissible leakage rate is less than 5 drops per minute. "
            "If leakage exceeds 10 drops per minute, replace the elastomer O-rings.\n\n"
            "## Section 2: Vibration Limits\n"
            "Normal vibration velocity is between 1.0 mm/s and 2.8 mm/s. "
            "Any reading above 4.5 mm/s signifies immediate bearing degradation."
        )

        chunks = document_chunker.chunk_document(
            text=text,
            document_id="doc_pump_manual",
            document_name="Pump_Manual.pdf"
        )
        assert len(chunks) >= 1

        # Verified upsert
        res = await qdrant_service.upsert_chunks_verified(
            chunks=chunks,
            collection_name="test_sovereign_knowledge"
        )
        assert res["success"] is True
        assert res["verified"] is True
        assert res["inserted_count"] == len(chunks)

        # Retrieval check
        hits = await qdrant_service.search(
            query="What is the permissible mechanical seal leakage rate?",
            collection_name="test_sovereign_knowledge",
            limit=2
        )
        assert len(hits) > 0
        assert any("leakage" in h["text"].lower() for h in hits)
    asyncio.run(_run())
