"""
Tests for Unified MemoryManager.
"""

import pytest
from memory.memory_manager import memory_manager


@pytest.mark.asyncio
async def test_memory_manager_health():
    health = await memory_manager.health_check()
    assert health is not None
    assert "memory" in health
    assert "stm" in health
    assert "ltm" in health
    assert "qdrant" in health
    assert "neo4j" in health
    assert "mem0" in health
    assert "ollama" in health
    assert "embedding_model" in health
    assert health["memory"] == "healthy"


@pytest.mark.asyncio
async def test_memory_manager_add_and_context():
    user_id = "test_user_mgr_01"
    fact = "The Sovereign AI Workbench is deployed completely on-premise without external cloud dependencies."

    # Add memory
    item = await memory_manager.add_memory(
        user_id=user_id,
        fact_or_preference=fact,
        memory_type="project_knowledge"
    )
    assert item is not None

    # Get enriched context
    ctx = await memory_manager.get_context(
        query="Where is the Sovereign AI Workbench deployed?",
        user_id=user_id
    )
    assert "on-premise" in ctx.lower() or "sovereign" in ctx.lower()


@pytest.mark.asyncio
async def test_memory_manager_search():
    user_id = "test_user_mgr_01"
    hits = await memory_manager.search(
        query="on-premise deployment",
        user_id=user_id,
        limit=2
    )
    assert isinstance(hits, list)
