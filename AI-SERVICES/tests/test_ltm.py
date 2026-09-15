"""
Tests for Long-Term Memory (LTM) subsystem.
"""

import pytest
from memory.ltm.ltm_manager import ltm_manager
from memory.ltm.memory_writer import memory_writer


def test_secret_filtering():
    assert memory_writer.contains_secrets("My password is password=Secret12345678") is True
    assert memory_writer.contains_secrets("Here is the key api_key=xkeysib-abc12345678") is True
    assert memory_writer.contains_secrets("Normal text: I like Python programming") is False

    sanitized = memory_writer.sanitize_text("Connect with mongodb://admin:admin@localhost:27017")
    assert "admin:admin" not in sanitized


def test_memory_classification():
    pref = memory_writer.classify_memory("I prefer Python over JavaScript")
    assert pref == "preference"

    rule = memory_writer.classify_memory("You must always validate input parameters")
    assert rule == "instruction"

    tech = memory_writer.classify_memory("The maintenance team uses vibration analysis for pump failure detection.")
    assert tech in ["technical_knowledge", "project_knowledge", "fact"]


@pytest.mark.asyncio
async def test_ltm_write_and_retrieve():
    user_id = "test_user_ltm_99"
    content = "The maintenance team uses vibration analysis for pump failure detection."

    item = await ltm_manager.add_memory(
        user_id=user_id,
        content=content,
        importance=0.9
    )
    assert item is not None
    assert item.user_id == user_id
    assert item.content == content

    # Retrieve context block
    context_block = await ltm_manager.get_context(
        query="How does the maintenance team detect pump failures?",
        user_id=user_id
    )
    assert "vibration analysis" in context_block.lower()
    assert "pump failure" in context_block.lower()
