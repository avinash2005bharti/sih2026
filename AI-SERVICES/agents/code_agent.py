"""
Code Agent for Sovereign AI Workbench.
Specialized in Python script generation, engineering calculations,
data transformations, and automated testing with qwen2.5-coder:3b.
"""

from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from core.config import settings
from core.logging import logger


class CodeAgent(BaseAgent):
    """Specialist agent for programming, engineering calculations, and script automation."""

    def __init__(self):
        super().__init__(
            name="Code Agent",
            description="Writes, reviews, and executes Python scripts for engineering automation, data processing, and verification.",
            model=settings.OLLAMA_CODE_MODEL,
            tools=["execute_python", "read_file", "write_file", "file_diff"]
        )

    def _get_system_message(self) -> str:
        return """You are the Lead Software & Automation Engineer.
Your responsibilities:
1. Write clean, robust, well-documented Python code
2. Solve engineering calculations, numerical algorithms, and data parsing
3. Use only Python standard libraries or specified sandbox modules
4. Write defensively with explicit type hints and error handling
5. When writing code, wrap executable blocks in standard ```python ... ``` fences."""

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


code_agent = CodeAgent()
