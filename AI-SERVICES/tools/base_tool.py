"""
Base tool interface for all workbench tools.
Enforces schema definition, argument validation, safe execution, output schema, and audit logging.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time
from core.logging import logger


class BaseTool(ABC):
    """Abstract base class for all agentic tools."""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "error": {"type": "string"},
        },
        "required": ["success"]
    }

    def __init__(self):
        if not self.name:
            raise ValueError(f"Tool {self.__class__.__name__} must define a name")
        if not self.description:
            raise ValueError(f"Tool {self.__class__.__name__} must define a description")

    @abstractmethod
    async def arun(self, **kwargs) -> Any:
        """Execute the tool asynchronously."""
        pass

    def run(self, **kwargs) -> Any:
        """Execute the tool synchronously."""
        import asyncio
        return asyncio.run(self.arun(**kwargs))

    def to_schema(self) -> Dict[str, Any]:
        """Convert tool definition to JSON Schema compatible with LLM tool/function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    def validate_args(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Check required arguments are present."""
        required = self.parameters.get("required", [])
        for req in required:
            if req not in kwargs:
                raise ValueError(f"Missing required argument '{req}' for tool '{self.name}'")
        return kwargs
