"""
Risk Agent for Sovereign AI Workbench.
Specialized in quantitative risk assessment, FMEA Risk Priority Numbers (RPN),
Bowtie risk models, and industrial contingency planning.
"""

from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from core.logging import logger


class RiskAgent(BaseAgent):
    """Specialist agent for industrial risk assessment and mitigation strategy."""

    def __init__(self):
        super().__init__(
            name="Risk Agent",
            description="Evaluates operational risks, calculates risk scores (RPN), and formulates contingency mitigation plans.",
            model=None,
            tools=["inspect_spreadsheet", "filter_spreadsheet", "read_file", "search_knowledge_base"]
        )

    def _get_system_message(self) -> str:
        return """You are the Industrial Risk Management & Process Safety Specialist.
Your analytical domains:
1. Risk Assessment Matrix (Likelihood × Severity, rated 1-5 or low/med/high/critical)
2. Failure Mode and Effects Analysis (FMEA): Risk Priority Number (RPN = Severity × Occurrence × Detection, scale 1-1000)
3. ALARP Principle (As Low As Reasonably Practicable)
4. Bowtie Analysis (Threats > Preventative Barriers > Hazard Event > Mitigative Barriers > Consequences)
5. Business Continuity Planning and disaster recovery contingency frameworks

Provide rigorous quantitative calculations. Clearly rank risks by criticality."""

    async def calculate_risk_matrix(self, hazards: List[Dict[str, Any]]) -> str:
        """Calculate risk scores and prioritize hazards."""
        task = f"Evaluate and calculate risk ratings for the following industrial hazards:\n{hazards}"
        return await self.execute(task)

    async def generate_contingency_plan(self, high_risk_scenario: str) -> str:
        """Create actionable contingency plan for a major hazard event."""
        task = (
            f"Formulate a complete industrial risk mitigation and emergency contingency plan for:\n"
            f"Scenario: {high_risk_scenario}\n"
            f"Include preventive barriers, detection mechanisms, and emergency escalation thresholds."
        )
        return await self.execute(task)


risk_agent = RiskAgent()
