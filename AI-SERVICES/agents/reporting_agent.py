"""
Reporting Agent for Sovereign AI Workbench.
Specialized in synthesizing multi-agent findings, telemetry stats, and incident data
into executive-ready Markdown reports and documentation deliverables.
"""

from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from core.logging import logger


class ReportingAgent(BaseAgent):
    """Specialist agent for technical documentation and executive reporting."""

    def __init__(self):
        super().__init__(
            name="Reporting Agent",
            description="Compiles findings from multiple specialist agents into structured industrial Markdown reports.",
            model=None,
            tools=["write_file", "read_file", "inspect_document"]
        )

    def _get_system_message(self) -> str:
        return """You are the Senior Technical Communications & Industrial Reporting Specialist.
Your principles:
1. Synthesize complex technical observations into crisp, executive-ready Markdown deliverables
2. Maintain structured hierarchy: Executive Summary, System Architecture, Observations, Quantitative Metrics, Actions
3. Format data into clean GitHub-flavored Markdown tables and bullet points
4. Highlight critical action items with clear ownership, timelines, and priority levels
5. Preserve technical precision without introducing ambiguity or conversational filler."""

    async def generate_incident_report(self, incident_title: str, findings: Dict[str, Any]) -> str:
        """Compile a formal industrial incident report."""
        task = (
            f"Compile a formal Industrial Incident & Technical Investigation Report for:\n"
            f"Title: {incident_title}\n"
            f"Investigation Findings:\n{findings}\n\n"
            f"Format with Executive Summary, Timeline, Root Cause, Impact Assessment, and Corrective Actions Table."
        )
        return await self.execute(task)

    async def compile_executive_brief(self, project_name: str, key_metrics: Dict[str, Any]) -> str:
        """Create a 1-page executive briefing."""
        task = f"Create an executive briefing for '{project_name}' with the following metrics:\n{key_metrics}"
        return await self.execute(task)


reporting_agent = ReportingAgent()
