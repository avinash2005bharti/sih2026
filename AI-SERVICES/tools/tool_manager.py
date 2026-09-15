"""
MCP (Model Context Protocol) Manager for Sovereign AI Workbench.
Handles discovery, registration, and dispatch for all MCP tools.
"""

import time
from typing import Any, Dict, List, Optional
from core.logging import logger

# MCP Tool Implementations
from tools.filesystem_mcp import filesystem_mcp_tools
from tools.python_mcp import python_mcp_tools
from tools.ocr_mcp import ocr_mcp_tools
from tools.vision_mcp import vision_mcp_tools
from tools.spreadsheet_mcp import spreadsheet_mcp_tools
from tools.document_mcp import document_mcp_tools
from tools.knowledge_mcp import knowledge_mcp_tools
from tools.memory_mcp import memory_mcp_tools
from tools.ppt_mcp import ppt_mcp_tools

class ToolManager:
    """Manages MCP tool registration and safe execution."""

    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._register_default_tools()

    def _register_default_tools(self):
        """Register all default built-in workbench MCP tools."""
        tool_collections = [
            filesystem_mcp_tools,
            python_mcp_tools,
            ocr_mcp_tools,
            vision_mcp_tools,
            spreadsheet_mcp_tools,
            document_mcp_tools,
            knowledge_mcp_tools,
            memory_mcp_tools,
            ppt_mcp_tools
        ]
        
        for collection in tool_collections:
            for tool_name, tool_func in collection.items():
                self.register_tool(tool_name, tool_func)

        logger.info(f"ToolManager initialized with {len(self._tools)} MCP tools.")

    def register_tool(self, name: str, tool_func: Any):
        """Register a new tool function."""
        self._tools[name] = tool_func

    def get_tool(self, name: str) -> Optional[Any]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List names of all registered MCP tools."""
        return list(self._tools.keys())

    def get_tools_prompt_description(self, tool_names: Optional[List[str]] = None) -> str:
        """Format a concise text description of available tools suitable for LLM system prompts."""
        targets = tool_names if tool_names is not None else self._tools.keys()
        lines = ["You have access to the following sovereign MCP tools:"]
        for name in targets:
            if name in self._tools:
                lines.append(f"- `{name}`")
        return "\n".join(lines)

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Safely execute a tool with timing, argument validation, and audit recording."""
        tool_func = self.get_tool(name)
        if not tool_func:
            err = f"Unknown tool: '{name}'. Available: {list(self._tools.keys())}"
            logger.error(err)
            return {"success": False, "error": err, "tool": name, "exit_code": 1}

        start_time = time.time()
        logger.info(f"Executing MCP tool '{name}' with arguments: {arguments}")

        try:
            # We assume tool_func is an async function
            result = await tool_func(**arguments)
            duration = time.time() - start_time

            res_obj = result if isinstance(result, dict) else {"output": str(result), "success": True}
            success = res_obj.get("success", True)
            exit_code = res_obj.get("exit_code", 0 if success else 1)

            record = {
                "tool": name,
                "arguments": arguments,
                "duration_seconds": round(duration, 3),
                "timestamp": time.time(),
                "success": success,
                "exit_code": exit_code
            }
            self._execution_history.append(record)

            logger.info(f"MCP Tool '{name}' completed in {duration:.3f}s (success={success})")
            return {
                "success": success,
                "tool": name,
                "duration_seconds": round(duration, 3),
                "exit_code": exit_code,
                "result": res_obj
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Execution error in MCP tool '{name}': {e}", exc_info=True)
            record = {
                "tool": name,
                "arguments": arguments,
                "duration_seconds": round(duration, 3),
                "timestamp": time.time(),
                "success": False,
                "exit_code": 1,
                "error": str(e)
            }
            self._execution_history.append(record)
            return {
                "success": False,
                "tool": name,
                "duration_seconds": round(duration, 3),
                "exit_code": 1,
                "error": str(e)
            }

tool_manager = ToolManager()
