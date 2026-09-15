"""
Tests for Qdrant Vector Service.
"""

import time
import pytest
from memory.vector.qdrant_service import qdrant_service
from memory.embeddings.embedding_service import embedding_service
from memory.models import MemoryItem


@pytest.mark.asyncio
async def test_qdrant_initialization_and_health():
    # Idempotent init
    init_success = await qdrant_service.initialize()
    assert init_success is True

    health = await qdrant_service.health_check()
    assert health["status"] == "healthy"
    assert health["collection_exists"] is True


@pytest.mark.asyncio
async def test_qdrant_upsert_and_search():
    await qdrant_service.initialize()
    user_id = "test_user_qdrant_1"
    content = "The engineering team uses Qdrant for semantic search."
    vector = await embedding_service.embed_text(content)
    assert len(vector) == 768

    item = MemoryItem(
        memory_id="test_mem_qdrant_42",
        user_id=user_id,
        content=content,
        memory_type="technical_knowledge",
        source="unit_test",
        created_at=time.time(),
        updated_at=time.time()
    )

    upsert_ok = await qdrant_service.upsert_memory(item, vector)
    assert upsert_ok is True

    # Search with user filter
    query_vector = await embedding_service.embed_text("What vector search tool is used?")
    hits = await qdrant_service.search_memories(
        query_vector=query_vector,
        user_id=user_id,
        limit=3,
        score_threshold=0.50
    )
    assert len(hits) >= 1
    assert any("Qdrant" in h["content"] for h in hits)

    # Cleanup
    await qdrant_service.delete_memory("test_mem_qdrant_42")
