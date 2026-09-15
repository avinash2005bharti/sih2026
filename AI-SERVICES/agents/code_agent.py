"""
Coding Agent for Sovereign AI Workbench.
Specialized in Python script generation, engineering calculations,
data transformations, and automated testing with qwen2.5-coder:1.5b.
"""

from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from core.logging import logger

class CodingAgent(BaseAgent):
    """Specialist agent for programming, engineering calculations, and script automation."""

    def __init__(self):
        super().__init__("CodingAgent")

    async def generate_script(self, requirement: str) -> str:
        """Generate a Python script for a specific requirement."""
        task = f"Write a complete, runnable Python script for the following task:\n{requirement}"
        return await self.execute(task)

    async def debug_code(self, code: str, error_message: str) -> str:
        """Debug code based on an error message."""
        task = (
            f"Debug and fix this Python code:\n```python\n{code}\n```\n\n"
            f"Observed Error:\n{error_message}\n\n"
            f"Provide the root cause and the corrected, runnable script."
        )
        return await self.execute(task)

coding_agent = CodingAgent()
