"""
Tests for Local Ollama Embedding Service.
"""

import pytest
from memory.embeddings.embedding_service import embedding_service


@pytest.mark.asyncio
async def test_embedding_service_health():
    health = await embedding_service.check_health()
    assert health is not None
    assert "status" in health
    assert "model" in health
    assert health["available"] is True


@pytest.mark.asyncio
async def test_dimension_detection():
    dim = await embedding_service.detect_dimension()
    assert dim == 768


@pytest.mark.asyncio
async def test_embed_single_text():
    text = "Sovereign On-Premise Agentic AI Workbench"
    vector = await embedding_service.embed_text(text)
    assert isinstance(vector, list)
    assert len(vector) == 768
    assert all(isinstance(v, (float, int)) for v in vector)


@pytest.mark.asyncio
async def test_embed_empty_text():
    vector = await embedding_service.embed_text("")
    assert vector == []
