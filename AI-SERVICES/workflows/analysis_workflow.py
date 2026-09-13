"""
Sovereign Analysis Workflow.
Task flow for data inspection, tabular filtering, statistical summaries, and metrics reporting.
"""

from typing import Any, Dict, Optional, List
from tools.spreadsheet_tool import SpreadsheetInspectTool, SpreadsheetFilterTool
from core.logging import logger


class AnalysisWorkflow:
    """Orchestrates CSV and tabular dataset analysis."""

    def __init__(self):
        self.inspect_tool = SpreadsheetInspectTool()
        self.filter_tool = SpreadsheetFilterTool()

    async def analyze_csv(self, file_path: str, sample_rows: int = 5) -> Dict[str, Any]:
        """Inspect structure, column statistics, and rows of a CSV."""
        return await self.inspect_tool.arun(file_path=file_path, sample_rows=sample_rows)

    async def filter_records(
        self,
        file_path: str,
        column: str,
        value: str,
        operator: str = "==",
        limit: int = 20
    ) -> Dict[str, Any]:
        """Filter rows by condition."""
        return await self.filter_tool.arun(
            file_path=file_path,
            column=column,
            value=value,
            operator=operator,
            limit=limit
        )


# Global singleton workflow
analysis_workflow = AnalysisWorkflow()
