import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from orchestrator.graph import agentic_workflow
from llm.ollama_client import ollama_client

def test_full_agentic_pdf_pipeline():
    async def _run():
        user_prompt = "Create a professional maintenance inspection report PDF from this document."

        with patch.object(ollama_client, "chat", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "success": True,
                "content": "Risk assessment completed. RPN calculated: Bearing Spalling=96, Seal Leak=180. Severity High.",
                "model": "qwen3:4b"
            }

            state = await agentic_workflow.run(
                user_request=user_prompt,
                conversation_id="conv_test_pdf",
                user_id="engineer_ayush",
                user_role="engineer"
            )

            assert state.is_complex_task is True
            assert len(state.plan) >= 2
            assert state.validation_verdict.valid is True
            assert len(state.artifacts) >= 1
            
            art = state.artifacts[0]
            assert art["type"] == "pdf"
            assert "maintenance" in art["filename"].lower()
            assert state.validation_verdict.score >= 80
            assert "Objective Completed" in state.final_response
    asyncio.run(_run())

def test_full_agentic_excel_pipeline():
    async def _run():
        user_prompt = "Create an Excel maintenance tracker for rotating machinery."

        with patch.object(ollama_client, "chat", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "success": True,
                "content": "Maintenance tracking schema prepared.",
                "model": "qwen3:4b"
            }

            state = await agentic_workflow.run(
                user_request=user_prompt,
                conversation_id="conv_test_xlsx",
                user_id="engineer_ayush",
                user_role="engineer"
            )

            assert state.is_complex_task is True
            assert state.validation_verdict.valid is True
            assert len(state.artifacts) >= 1
            
            art = state.artifacts[0]
            assert art["type"] in ["xlsx", "spreadsheet"]
            assert state.validation_verdict.score >= 80
    asyncio.run(_run())
