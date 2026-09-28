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

        try:
            from tools.spreadsheet_tool import inspect_spreadsheet_tool, filter_spreadsheet_tool
            self.register_tool("inspect_spreadsheet", inspect_spreadsheet_tool)
            self.register_tool("filter_spreadsheet", filter_spreadsheet_tool)
        except Exception as e:
            logger.debug(f"Spreadsheet tool registration notice: {e}")

        try:
            from tools.file_tool import write_file_tool, read_file_tool, list_directory_tool, diff_file_tool
            self.register_tool("write_file", write_file_tool)
            self.register_tool("read_file", read_file_tool)
            self.register_tool("list_directory", list_directory_tool)
            self.register_tool("file_diff", diff_file_tool)
        except Exception as e:
            logger.debug(f"File tool registration notice: {e}")

        try:
            from tools.code_tool import PythonExecutionTool
            self.register_tool("execute_python", PythonExecutionTool())
        except Exception as e:
            logger.debug(f"Code tool registration notice: {e}")

        try:
            from tools.document_tool import DocumentInspectTool, DocumentExtractTool
            self.register_tool("inspect_document", DocumentInspectTool())
            self.register_tool("extract_document_sections", DocumentExtractTool())
        except Exception as e:
            logger.debug(f"Document tool registration notice: {e}")

        try:
            from tools.rag_tool import search_knowledge_base
            self.register_tool("search_knowledge_base", search_knowledge_base)
        except Exception as e:
            logger.debug(f"RAG tool registration notice: {e}")

        try:
            from tools.pdf_tool import PDFCreatorTool
            self.register_tool("pdf_creator", PDFCreatorTool())
        except Exception as e:
            logger.debug(f"PDFCreatorTool registration notice: {e}")

        try:
            from tools.document_tool import DocumentCreatorTool
            self.register_tool("docx_creator", DocumentCreatorTool())
        except Exception as e:
            logger.debug(f"DocumentCreatorTool registration notice: {e}")

        try:
            from tools.spreadsheet_tool import SpreadsheetCreatorTool
            self.register_tool("xlsx_creator", SpreadsheetCreatorTool())
        except Exception as e:
            logger.debug(f"SpreadsheetCreatorTool registration notice: {e}")

        try:
            from tools.validators.pdf_validator import validate_pdf_artifact
            self.register_tool("pdf_validator", validate_pdf_artifact)
        except Exception as e:
            logger.debug(f"pdf_validator registration notice: {e}")

        try:
            from tools.validators.xlsx_validator import validate_xlsx_artifact
            self.register_tool("xlsx_validator", validate_xlsx_artifact)
        except Exception as e:
            logger.debug(f"xlsx_validator registration notice: {e}")

        try:
            from tools.validators.docx_validator import validate_docx_artifact
            self.register_tool("docx_validator", validate_docx_artifact)
        except Exception as e:
            logger.debug(f"docx_validator registration notice: {e}")

        # Common planning aliases
        if "read_file" in self._tools:
            self.register_tool("file_reader", self._tools["read_file"])
        if "write_file" in self._tools:
            self.register_tool("file_writer", self._tools["write_file"])

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
        alias_map = {
            "file_reader": "read_file",
            "file_writer": "write_file",
            "pdf_generator": "pdf_creator",
            "excel_creator": "xlsx_creator",
            "word_creator": "docx_creator",
        }
        if name in alias_map and alias_map[name] in self._tools:
            return self._tools[alias_map[name]]
        cleaned = name.lower().strip().replace("-", "_")
        if cleaned in self._tools:
            return self._tools[cleaned]
        if cleaned in alias_map and alias_map[cleaned] in self._tools:
            return self._tools[alias_map[cleaned]]
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

    async def execute_tool(self, name: str, arguments: Dict[str, Any], user_role: Optional[str] = None) -> Dict[str, Any]:
        """Safely execute a tool with timing, argument validation, and audit recording."""
        if user_role:
            try:
                from core.security import verify_rbac_permission
                if not verify_rbac_permission(user_role, name):
                    return {
                        "status": "error",
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": f"User role '{user_role}' denied access to tool '{name}'."
                    }
            except Exception as e:
                logger.debug(f"RBAC check notice: {e}")

        # 1. Try central tool registry first for standardized tools
        try:
            from tools.tool_registry import central_tool_registry
            if central_tool_registry.get_tool(name):
                res = await central_tool_registry.execute_tool(name, arguments)
                if isinstance(res, dict):
                    if "status" not in res:
                        res["status"] = "success" if res.get("success", False) else "error"
                    return res
        except ImportError:
            pass

        tool_func = self.get_tool(name)
        if not tool_func:
            err = f"Unknown tool: '{name}'. Available: {self.list_tools()}"
            logger.error(err)
            return {
                "status": "error",
                "error": "TOOL_NOT_FOUND",
                "success": False,
                "message": err,
                "tool": name,
                "exit_code": 1
            }

        start_time = time.time()
        logger.info(f"Executing MCP tool '{name}' with arguments: {arguments}")

        try:
            import inspect
            if hasattr(tool_func, "ainvoke"):
                result = await tool_func.ainvoke(arguments)
            elif hasattr(tool_func, "invoke"):
                result = tool_func.invoke(arguments)
            elif hasattr(tool_func, "arun"):
                try:
                    result = await tool_func.arun(**arguments)
                except TypeError:
                    result = await tool_func.arun(tool_input=arguments)
            elif inspect.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                result = tool_func(**arguments)

            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except Exception:
                    result = {"result": result, "success": True}

            if isinstance(result, dict) and "result" in result and isinstance(result["result"], str):
                try:
                    inner = json.loads(result["result"])
                    if isinstance(inner, dict):
                        result = {**result, **inner}
                except Exception:
                    pass
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
            ret = {
                "status": "success" if success else "error",
                "success": success,
                "tool": name,
                "duration_seconds": round(duration, 3),
                "exit_code": exit_code,
                "result": res_obj
            }
            # Flatten top-level keys from res_obj for convenience
            for k, v in res_obj.items():
                if k not in ret:
                    ret[k] = v
            return ret

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
                "status": "error",
                "success": False,
                "tool": name,
                "duration_seconds": round(duration, 3),
                "exit_code": 1,
                "error": str(e)
            }

tool_manager = ToolManager()
