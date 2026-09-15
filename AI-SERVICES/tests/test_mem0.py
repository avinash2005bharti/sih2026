"""
Tests for Mem0 Service.
"""

import pytest
from memory.mem0.mem0_service import mem0_service


@pytest.mark.asyncio
async def test_mem0_health():
    health = await mem0_service.health_check()
    assert health is not None
    assert health["status"] == "healthy"
    assert health["collection"] == "sovereign_ai_memory"


@pytest.mark.asyncio
async def test_mem0_add_and_search():
    user_id = "test_user_mem0_alpha"
    fact = "The user prefers FastAPI for microservices architecture."

    # Add memory
    res = await mem0_service.add_memory(
        text_or_messages=fact,
        user_id=user_id
    )
    assert res is not None

    # Search memory
    hits = await mem0_service.search_memories(
        query="What framework does the user prefer for microservices?",
        user_id=user_id,
        limit=3
    )
    assert len(hits) >= 1
    assert any("FastAPI" in h["memory"] for h in hits)
