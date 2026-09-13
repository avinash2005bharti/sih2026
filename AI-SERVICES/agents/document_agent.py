"""
Document Agent for Sovereign AI Workbench.
Specialized in analyzing documents, technical specifications, manuals,
and extracting structured information.
Also re-exports specialist agents for backward compatibility.
"""

from typing import Any, Dict, Optional, List
from agents.base_agent import BaseAgent
from core.logging import logger

# Import specialized agents for clean re-export
from agents.maintenance_agent import MaintenanceAgent, maintenance_agent
from agents.safety_agent import SafetyAgent, safety_agent
from agents.compliance_agent import ComplianceAgent, compliance_agent
from agents.risk_agent import RiskAgent, risk_agent
from agents.reporting_agent import ReportingAgent, reporting_agent
from agents.code_agent import CodeAgent, code_agent


class DocumentAgent(BaseAgent):
    """Agent specialized for technical document analysis and information extraction."""

    def __init__(self):
        super().__init__(
            name="Document Agent",
            description="Analyzes technical documents, manuals, and reports; extracts specifications, entities, and answers questions.",
            model=None,
            tools=["inspect_document", "extract_document_sections", "read_file", "write_file", "create_pdf", "search_knowledge_base"]
        )

    def _get_system_message(self) -> str:
        return """You are the Senior Technical Documentation Analyst.
Your core capabilities:
1. Thorough technical manual inspection and specification extraction
2. Answering domain questions with precise citations from source material
3. Identifying discrepancies between operational logs and technical manuals
4. Structured information extraction (operating limits, serial codes, part numbers)
5. Synthesizing dense documentation into concise executive summaries
6. Creating structured documents and reports using the write_file and create_pdf tools. When asked to create a document, ALWAYS use these tools to save the output instead of just printing it.

Always cite section headers, page numbers, or line numbers where available."""

    async def summarize(self, document: str, max_length: Optional[int] = None) -> str:
        """Summarize a document."""
        length_hint = f" (approximately {max_length} words)" if max_length else ""
        task = f"Please summarize this document{length_hint}:\n\n{document}"
        return await self.execute(task)

    async def answer_question(self, document: str, question: str) -> str:
        """Answer a question about a document."""
        context = {
            "document": document[:2000],
            "question": question
        }
        task = f"Given the provided document, please answer this question precisely: {question}\n\nDocument:\n{document}"
        return await self.execute(task, context)

    async def extract_specifications(self, document: str) -> Dict[str, Any]:
        """Extract technical specifications, tolerances, and operational thresholds."""
        task = (
            "Extract all technical specifications, operational limits (temperature, pressure, RPM), "
            f"and component part numbers from this document:\n\n{document}"
        )
        response = await self.execute(task)
        return {
            "specifications": response,
            "document_length": len(document)
        }


document_agent = DocumentAgent()

__all__ = [
    "DocumentAgent",
    "document_agent",
    "MaintenanceAgent",
    "maintenance_agent",
    "SafetyAgent",
    "safety_agent",
    "ComplianceAgent",
    "compliance_agent",
    "RiskAgent",
    "risk_agent",
    "ReportingAgent",
    "reporting_agent",
    "CodeAgent",
    "code_agent"
]
