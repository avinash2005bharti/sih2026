"""
Safety Agent for Sovereign AI Workbench.
Specialized in industrial workplace health and safety (EHS), OSHA standards,
hazard identification, and hierarchy-of-controls mitigation plans.
"""

from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from core.logging import logger


class SafetyAgent(BaseAgent):
    """Specialist agent for industrial safety and hazard mitigation."""

    def __init__(self):
        super().__init__(
            name="Safety Agent",
            description="Analyzes workplace safety reports, identifies physical/chemical hazards, and enforces EHS protocols.",
            model=None,
            tools=["search_knowledge_base", "read_file", "extract_document_sections"]
        )

    def _get_system_message(self) -> str:
        return """You are the Principal Industrial Environmental Health & Safety (EHS) Officer.
Your core mandates:
1. Identify immediate physical, chemical, electrical, and ergonomic hazards
2. Apply the Hierarchy of Controls (Elimination > Substitution > Engineering Controls > Administrative Controls > PPE)
3. Ensure strict compliance with OSHA standards (e.g. 1910.147 LOTO, 1910.1200 HazCom, 1910.134 Respiratory)
4. Conduct incident root-cause investigations
5. Author actionable Job Safety Analyses (JSA) and Safe Operating Procedures (SOP)

Worker life safety is paramount. Highlight critical hazards with immediate stop-work criteria."""

    async def evaluate_hazard(self, incident_or_scenario: str) -> str:
        """Evaluate a workplace safety hazard and determine severity and control measures."""
        task = f"Evaluate this industrial safety scenario, identify all hazards, and prescribe control measures:\n{incident_or_scenario}"
        return await self.execute(task)

    async def generate_jsa(self, task_name: str, steps: List[str]) -> str:
        """Generate a Job Safety Analysis table for a specific job."""
        task = (
            f"Generate a comprehensive Job Safety Analysis (JSA) for: '{task_name}'.\n"
            f"Task steps:\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)]) +
            "\nProvide columns: Step, Potential Hazards, Preventative Controls, Required PPE."
        )
        return await self.execute(task)


safety_agent = SafetyAgent()
