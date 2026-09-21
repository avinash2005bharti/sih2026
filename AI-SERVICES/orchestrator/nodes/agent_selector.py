"""
Agent Selector Node for Sovereign Agentic Orchestrator.
Matches the current plan step to the best specialized agent and model from the model registry.
"""

from orchestrator.state import AgenticState
from llm.model_registry import model_registry
from core.logging import logger

# Mapping of aliases and keywords to standardized specialist roles
ROLE_ALIASES = {
    "code": "coding",
    "coding": "coding",
    "code_agent": "coding",
    "python": "coding",
    "developer": "coding",

    "doc": "document",
    "document": "document",
    "document_agent": "document",
    "text": "document",
    "manual": "document",

    "risk": "risk",
    "risk_agent": "risk",
    "hazard": "risk",
    "fmea": "risk",

    "compliance": "compliance",
    "compliance_agent": "compliance",
    "iso": "compliance",
    "regulatory": "compliance",
    "audit": "compliance",

    "safety": "safety",
    "safety_agent": "safety",
    "osha": "safety",

    "maintenance": "maintenance",
    "maintenance_agent": "maintenance",
    "telemetry": "maintenance",
    "sensor": "maintenance",

    "reporting": "reporting",
    "reporting_agent": "reporting",
    "report": "reporting",
    "synthesizer": "reporting",

    "vision": "vision",
    "vision_agent": "vision",
    "image": "vision",
    "camera": "vision",

    "general": "general",
    "chat": "general",
}


class AgentSelectorNode:
    """Selects the specialized agent and open-weight model for the current step."""

    async def execute(self, state: AgenticState) -> AgenticState:
        if not state.plan or state.current_step_index >= len(state.plan):
            state.selected_agent = "reporting"
            state.selected_model = model_registry.get_model("reporting")
            return state

        current_step = state.plan[state.current_step_index]
        target = current_step.target_agent.lower().strip()

        # Normalize target agent name using aliases
        normalized_agent = "general"
        for alias, canon in ROLE_ALIASES.items():
            if alias in target or target in alias:
                normalized_agent = canon
                break

        # Resolve model from centralized model registry
        selected_model = model_registry.get_model(normalized_agent)

        state.selected_agent = normalized_agent
        state.selected_model = selected_model

        logger.info(
            f"[AGENT_SELECTOR] Step {current_step.step_number} ('{current_step.title}') "
            f"-> Agent: '{normalized_agent}', Model: '{selected_model}'"
        )
        return state

