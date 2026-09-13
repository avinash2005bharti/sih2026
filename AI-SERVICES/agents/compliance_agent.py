"""
Compliance Agent for Sovereign AI Workbench.
Specialized in regulatory verification, ISO standards (9001, 14001, 45001, 27001),
gap analyses, and industrial audit preparation.
"""

from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from core.logging import logger


class ComplianceAgent(BaseAgent):
    """Specialist agent for industrial regulatory compliance and standards."""

    def __init__(self):
        super().__init__(
            name="Compliance Agent",
            description="Reviews industrial documentation against regulatory standards and conducts gap analyses.",
            model=None,
            tools=["search_knowledge_base", "read_file", "extract_document_sections", "inspect_document"]
        )

    def _get_system_message(self) -> str:
        return """You are the Chief Regulatory & Standards Compliance Auditor.
Your core expertise:
1. ISO Standards: ISO 9001 (Quality Management), ISO 14001 (Environmental), ISO 45001 (Safety), ISO 27001 (Security)
2. Regulatory frameworks (EPA, ASME, API, NFPA, IEC, local industrial mandates)
3. Gap analysis: comparing existing company procedures against mandated standards
4. Audit Readiness: generating non-conformance reports (NCR) and corrective action plans (CAPA)
5. Strict evidentiary verification: requiring specific clause references (e.g. ISO 9001:2015 Clause 8.5.1)

Maintain uncompromising objectivity. Clearly delineate between mandatory requirements and best-practice recommendations."""

    async def check_compliance(self, document_content: str, standard: str) -> str:
        """Evaluate document against a standard."""
        task = f"Audit the following operational documentation against the requirements of standard '{standard}':\n\n{document_content}"
        return await self.execute(task)

    async def audit_gap_analysis(self, procedure_text: str, target_standard: str) -> str:
        """Perform gap analysis and create CAPA plan."""
        task = (
            f"Perform a comprehensive compliance gap analysis for standard '{target_standard}'.\n"
            f"Existing procedure:\n{procedure_text}\n\n"
            f"Identify: 1) Compliant elements, 2) Deficiencies / Non-conformances, 3) Corrective Action Plan (CAPA)."
        )
        return await self.execute(task)


compliance_agent = ComplianceAgent()
