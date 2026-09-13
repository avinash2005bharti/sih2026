"""
Router Node for Sovereign Agentic Orchestrator.
Classifies whether a user query requires a direct conversational answer
or a multi-step agentic plan with tool execution.
"""

import re
from orchestrator.state import AgenticState
from llm.model_router import model_router
from core.logging import logger
from core.config import settings

# Keywords indicating need for tool execution or industrial multi-step workflow
ACTION_KEYWORDS = [
    "analyze", "inspect", "read", "write", "create file", "run", "execute",
    "calculate", "troubleshoot", "csv", "data", "report", "incident", "failure",
    "hazard", "compliance", "safety", "standard", "iso", "vibration", "sensor",
    "telemetry", "log", "script", "code", "python", "diff", "search doc", "manual"
]

SIMPLE_GREETINGS = [
    "hello", "hi", "hey", "good morning", "good afternoon", "who are you", "what can you do", "help"
]


class RouterNode:
    """Routes incoming user requests to direct response or agentic planning."""

    async def execute(self, state: AgenticState) -> AgenticState:
        query = state.user_query.strip()
        query_lower = query.lower()

        logger.info(f"RouterNode evaluating query: '{query[:80]}...'")

        # 1. Check for simple greetings
        if query_lower in SIMPLE_GREETINGS or (len(query_lower.split()) <= 2 and any(g in query_lower for g in ["hi", "hello", "hey"])):
            state.route = "direct"
            state.is_direct_chat = True
            state.status = "routing"
            state.selected_model = model_router.models.get("chat", settings.OLLAMA_CHAT_MODEL)
            logger.info("RouterNode routed to: direct (simple greeting)")
            return state

        # 2. Check for explicit action keywords
        has_action = any(re.search(rf"\b{re.escape(kw)}\b", query_lower) for kw in ACTION_KEYWORDS)

        # Questions like "What is OSHA 1910?" or "Explain predictive maintenance" can be answered directly if short,
        # but if the user says "inspect", "run", "calculate", "check my file", it requires the agentic engine.
        requires_tools = any(kw in query_lower for kw in ["file", "csv", "run", "execute", "script", "code", "calculate", "diff", "inspect"])

        if has_action or requires_tools or len(query.split()) > 15:
            state.route = "agentic"
            state.is_direct_chat = False
            state.status = "planning"
            logger.info("RouterNode routed to: agentic (workflow / tools required)")
        else:
            state.route = "direct"
            state.is_direct_chat = True
            state.status = "routing"
            state.selected_model = model_router.models.get("chat", settings.OLLAMA_CHAT_MODEL)
            logger.info("RouterNode routed to: direct (conversational)")

        return state
