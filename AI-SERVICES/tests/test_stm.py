"""
Tests for Short-Term Memory (STM) subsystem.
"""

import pytest
from memory.stm.stm_manager import stm_manager
from memory.stm.context_builder import context_builder
from memory.models import STMContext, STMMessage


@pytest.mark.asyncio
async def test_stm_health():
    health = await stm_manager.health_check()
    assert health is not None
    assert health["status"] in ["healthy", "degraded"]


@pytest.mark.asyncio
async def test_stm_fallback_caching():
    conv_id = "test_conv_fallback_01"
    stm_manager.record_message_fallback(conv_id, "user", "Hello assistant")
    stm_manager.record_message_fallback(conv_id, "assistant", "Hello! How can I help you today?")

    ctx = await stm_manager.get_conversation_context(conv_id)
    assert len(ctx.messages) >= 2
    assert ctx.messages[0].role == "user"
    assert ctx.messages[1].role == "assistant"

    # Context builder formatting
    prompt_str = context_builder.format_history_for_prompt(ctx, current_query="Next query")
    assert "User: Hello assistant" in prompt_str
    assert "Assistant: Hello! How can I help you today?" in prompt_str

    # Clean up
    stm_manager.clear_context(conv_id)


def test_context_builder_message_exclusion():
    ctx = STMContext(
        conversation_id="conv_123",
        messages=[
            STMMessage(role="user", content="First message"),
            STMMessage(role="assistant", content="First response"),
            STMMessage(role="user", content="Current message")
        ]
    )
    # The current message should be excluded from historical context if passed as current_query
    formatted = context_builder.format_history_for_prompt(ctx, current_query="Current message")
    assert "First message" in formatted
    assert "First response" in formatted
    assert "Current message" not in formatted
