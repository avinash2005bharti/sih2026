"""
Router Node for Sovereign Agentic Orchestrator.
Uses the two-tier SLM Model Router to classify intent, agent role, and workflow mode.
"""

import re
from orchestrator.state import AgenticState
from llm.model_router import model_router
from llm.model_registry import model_registry
from core.logging import logger


class RouterNode:
    """Routes incoming user requests to direct response or agentic planning."""

    async def execute(self, state: AgenticState) -> AgenticState:
        query = state.user_query.strip()
        logger.info(f"[ROUTER] Evaluating task: '{query[:80]}...'")

        # Check if user query mentions images or uploaded files
        has_image = bool(re.search(r"\.(?:png|jpg|jpeg|bmp|webp)", query, re.IGNORECASE))

        # Invoke two-tier structured router (deterministic rule-based -> structured SLM router)
        route_decision = await model_router.route_request(query, has_image=has_image)
        logger.info(f"[ROUTER] Decision: intent='{route_decision['intent']}' agent='{route_decision['agent']}' confidence={route_decision.get('confidence', 0.0)}")

        intent = route_decision.get("intent", "general")
        requires_rag = route_decision.get("requires_rag", False)
        requires_code = route_decision.get("requires_code", False)
        requires_doc = route_decision.get("requires_document", False)

        # Simple conversational queries without rag or tools bypass multi-step planning
        if intent == "general" and not (requires_rag or requires_code or requires_doc):
            state.route = "direct"
            state.is_direct_chat = True
            state.status = "routing"
            state.selected_agent = "general"
            state.selected_model = model_registry.get_model("general")
            logger.info("[ROUTER] Routed to: direct (conversational SLM)")
            return state

        # Industrial tasks require agentic planning and specialist execution
        state.route = "agentic"
        state.is_direct_chat = False
        state.status = "planning"
        state.selected_agent = route_decision.get("agent", "general").replace("_agent", "")
        state.selected_model = model_registry.get_model(state.selected_agent)
        logger.info(f"[ROUTER] Routed to: agentic (Specialist: '{state.selected_agent}', Model: '{state.selected_model}')")

        return state

