"""
Tests for Neo4j Knowledge Graph Service.
"""

import pytest
from memory.graph.neo4j_service import neo4j_service


@pytest.mark.asyncio
async def test_neo4j_health():
    health = await neo4j_service.health_check()
    assert health is not None
    assert health["status"] == "healthy"


@pytest.mark.asyncio
async def test_neo4j_record_memory_and_query():
    user_id = "test_user_neo_1"
    memory_id = "mem_neo_test_99"
    content = "The user prefers Python for machine learning workflows."
    entities = ["Python", "machine learning"]

    ok = await neo4j_service.record_memory(
        memory_id=memory_id,
        user_id=user_id,
        content=content,
        memory_type="preference",
        entities=entities
    )
    assert ok is True

    # Query graph
    results = await neo4j_service.query_related_context(
        query="What does user prefer for Python workflows?",
        user_id=user_id,
        limit=5
    )
    assert len(results) >= 1
    assert any("Python" in str(r) for r in results)


@pytest.mark.asyncio
async def test_neo4j_task_execution_tracking():
    task_ok = await neo4j_service.record_task_execution(
        task_id="task_test_neo_01",
        task_type="risk_assessment",
        tool_name="paddle_ocr"
    )
    assert task_ok is True
