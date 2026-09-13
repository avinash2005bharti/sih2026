"""
Sovereign Document Workflow.
Task flow for document summarization, PDF generation, and confidential knowledge retrieval.
"""

import time
from typing import Any, Dict, Optional, List
from tools.document_tool import GeneratePDFTool, DocumentInspectTool
from tools.rag_tool import KnowledgeSearchTool
from core.logging import logger


class DocumentWorkflow:
    """Orchestrates document search, inspection, and PDF generation."""

    def __init__(self):
        self.search_tool = KnowledgeSearchTool()
        self.inspect_tool = DocumentInspectTool()
        self.pdf_tool = GeneratePDFTool()

    async def generate_report_pdf(self, title: str, content: str, file_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate a formal PDF document inside the sandbox reports/ directory."""
        clean_name = file_name or f"{title.lower().replace(' ', '_')[:30]}.pdf"
        res = await self.pdf_tool.arun(file_name=clean_name, title=title, content=content)
        return res

    async def research_and_summarize(self, topic: str, top_k: int = 4) -> Dict[str, Any]:
        """Search the knowledge base for relevant document sections."""
        res = await self.search_tool.arun(query=topic, top_k=top_k)
        return res


# Global singleton workflow
document_workflow = DocumentWorkflow()
