"""
Agent Selector Node for Sovereign Agentic Orchestrator.
Matches the current plan step to the best specialized agent and model.
"""

from orchestrator.state import AgenticState
from core.config import settings
from core.logging import logger

AGENT_MODEL_MAPPING = {
    "code_agent": settings.OLLAMA_CODE_MODEL,
    "maintenance_agent": settings.OLLAMA_CHAT_MODEL,
    "safety_agent": settings.OLLAMA_CHAT_MODEL,
    "compliance_agent": settings.OLLAMA_CHAT_MODEL,
    "risk_agent": settings.OLLAMA_CHAT_MODEL,
    "reporting_agent": settings.OLLAMA_CHAT_MODEL,
    "document_agent": settings.OLLAMA_CHAT_MODEL,
}


class AgentSelectorNode:
    """Selects the specialized agent and open-weight model for the current step."""

    async def execute(self, state: AgenticState) -> AgenticState:
        if not state.plan or state.current_step_index >= len(state.plan):
            state.selected_agent = "reporting_agent"
            state.selected_model = settings.OLLAMA_CHAT_MODEL
            return state

        current_step = state.plan[state.current_step_index]
        target = current_step.target_agent.lower().strip()

        # Normalize target agent name
        normalized_agent = "document_agent"
        for key in AGENT_MODEL_MAPPING.keys():
            if key in target or target in key:
                normalized_agent = key
                break

        state.selected_agent = normalized_agent
        state.selected_model = AGENT_MODEL_MAPPING.get(normalized_agent, settings.OLLAMA_CHAT_MODEL)

        logger.info(
            f"AgentSelectorNode assigned Step {current_step.step_number} ('{current_step.title}') "
            f"-> Agent: '{state.selected_agent}', Model: '{state.selected_model}'"
        )
        return state
