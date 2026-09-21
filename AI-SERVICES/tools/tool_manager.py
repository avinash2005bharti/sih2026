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
        """Retrieve a tool by name or alias."""
        if not name or not isinstance(name, str):
            return None
        if name in self._tools:
            return self._tools[name]
        cleaned = name.lower().strip().replace("-", "_")
        if cleaned in self._tools:
            return self._tools[cleaned]
        cleaned_dot = name.lower().strip().replace("_", ".")
        if cleaned_dot in self._tools:
            return self._tools[cleaned_dot]
        try:
            from tools.tool_registry import central_tool_registry
            t = central_tool_registry.get_tool(name)
            if t:
                return t
        except ImportError:
            pass
        try:
            from tools.agent_tools import resolve_tool
            return resolve_tool(name)
        except ImportError:
            pass
        return None

    def list_tools(self) -> List[str]:
        """List names of all registered MCP and sovereign tools."""
        names = set(self._tools.keys())
        try:
            from tools.tool_registry import central_tool_registry
            names.update(central_tool_registry.list_tools())
        except ImportError:
            pass
        return sorted(list(names))

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return tool schemas for planning and specialist agents."""
        try:
            from tools.tool_registry import central_tool_registry
            return central_tool_registry.list_tool_definitions()
        except ImportError:
            return [{"name": name} for name in self._tools.keys()]

    def get_tools_prompt_description(self, tool_names: Optional[List[str]] = None) -> str:
        """Format a concise text description of available tools suitable for LLM system prompts."""
        targets = tool_names if tool_names is not None else self.list_tools()
        lines = ["You have access to the following sovereign tools:"]
        for name in targets:
            lines.append(f"- `{name}`")
        return "\n".join(lines)

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Safely execute a tool with timing, argument validation, and audit recording."""
        # 1. Try central tool registry first for standardized tools
        try:
            from tools.tool_registry import central_tool_registry
            if central_tool_registry.get_tool(name):
                return await central_tool_registry.execute_tool(name, arguments)
        except ImportError:
            pass

        tool_func = self.get_tool(name)
        if not tool_func:
            err = f"Unknown tool: '{name}'. Available: {self.list_tools()}"
            logger.error(err)
            return {"success": False, "error": err, "tool": name, "exit_code": 1}

        start_time = time.time()
        logger.info(f"Executing MCP tool '{name}' with arguments: {arguments}")

        try:
            import inspect
            if hasattr(tool_func, "arun"):
                result = await tool_func.arun(**arguments)
            elif hasattr(tool_func, "invoke"):
                result = tool_func.invoke(arguments)
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except Exception:
                        result = {"result": result, "success": True}
            elif inspect.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                result = tool_func(**arguments)
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
