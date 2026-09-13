"""
Central Tool Manager for Sovereign AI Workbench.
Handles discovery, registration, JSON Schema export, audit logging,
manifest export, and safe execution dispatch for all workbench tools.
"""

import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from tools.base_tool import BaseTool

# File tools
from tools.file_tool import (
    ReadFileTool, WriteFileTool, CreateDirectoryTool,
    DeleteFileTool, MoveFileTool, PatchFileTool,
    ListDirectoryTool, FileDiffTool
)

# Code & Execution tools
from tools.code_tool import PythonExecutionTool, ControlledCommandTool

# Document tools
from tools.document_tool import GeneratePDFTool, DocumentInspectTool, DocumentExtractTool

# Spreadsheet tools
from tools.spreadsheet_tool import (
    SpreadsheetInspectTool, SpreadsheetFilterTool, SpreadsheetWriteTool
)

# RAG tools
from tools.rag_tool import KnowledgeSearchTool, IndexDocumentTool

from core.logging import logger

TOOLS_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = TOOLS_DIR / "tools_registry.json"


class ToolManager:
    """Manages tool registration, schema generation, manifest export, and safe execution."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._aliases: Dict[str, str] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._register_default_tools()
        self._export_registry_manifest()

    def _register_default_tools(self):
        """Register all default built-in workbench tools."""
        default_tools = [
            # File system tools
            ReadFileTool(),
            WriteFileTool(),
            CreateDirectoryTool(),
            DeleteFileTool(),
            MoveFileTool(),
            PatchFileTool(),
            ListDirectoryTool(),
            FileDiffTool(),
            # Code execution
            PythonExecutionTool(),
            ControlledCommandTool(),
            # Document analysis & PDF
            GeneratePDFTool(),
            DocumentInspectTool(),
            DocumentExtractTool(),
            # Tabular & spreadsheet
            SpreadsheetInspectTool(),
            SpreadsheetFilterTool(),
            SpreadsheetWriteTool(),
            # Knowledge base
            KnowledgeSearchTool(),
            IndexDocumentTool(),
        ]
        for t in default_tools:
            self.register_tool(t)

        # Register aliases for model function-calling compatibility
        self.register_alias("create_file", "write_file")
        self.register_alias("list_files", "list_directory")
        self.register_alias("execute_code", "execute_python")
        self.register_alias("python.execute", "execute_python")
        self.register_alias("file.create", "write_file")
        self.register_alias("file.read", "read_file")
        self.register_alias("file.list", "list_directory")
        self.register_alias("pdf.create", "create_pdf")

        logger.info(f"ToolManager initialized with {len(self._tools)} tools: {list(self._tools.keys())}")

    def register_tool(self, tool: BaseTool):
        """Register a new tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool registration: {tool.name}")
        self._tools[tool.name] = tool

    def register_alias(self, alias_name: str, target_name: str):
        """Register an alternative name or alias for an existing tool."""
        self._aliases[alias_name] = target_name

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by canonical name or alias."""
        target = self._aliases.get(name, name)
        return self._tools.get(target)

    def list_tools(self) -> List[str]:
        """List canonical names of all registered tools."""
        return list(self._tools.keys())

    def get_schemas(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Export OpenAI/Ollama compatible function/tool schemas.
        If tool_names is provided, returns schemas only for requested tools.
        """
        targets = tool_names if tool_names is not None else self._tools.keys()
        schemas = []
        for name in targets:
            tool = self.get_tool(name)
            if tool:
                schemas.append(tool.to_schema())
        return schemas

    def _export_registry_manifest(self):
        """Export machine-readable tools manifest to tools_registry.json."""
        try:
            manifest = {
                "version": "1.0.0",
                "system": "Sovereign AI Workbench",
                "total_tools": len(self._tools),
                "tools": {}
            }
            for name, tool in self._tools.items():
                manifest["tools"][name] = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "output_schema": getattr(tool, "output_schema", {})
                }
            with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Exported tools manifest to {REGISTRY_FILE}")
        except Exception as e:
            logger.warning(f"Failed to export tools_registry.json: {e}")

    def get_tools_prompt_description(self, tool_names: Optional[List[str]] = None) -> str:
        """
        Format a concise text description of available tools suitable for LLM system prompts.
        """
        targets = tool_names if tool_names is not None else self._tools.keys()
        lines = ["You have access to the following sovereign tools:"]
        for name in targets:
            tool = self.get_tool(name)
            if tool:
                params = tool.parameters.get("properties", {})
                req = tool.parameters.get("required", [])
                params_str = ", ".join([f"{k}*" if k in req else k for k in params.keys()])
                lines.append(f"- `{tool.name}({params_str})`: {tool.description}")
        return "\n".join(lines)

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely execute a tool with timing, argument validation, and audit recording.
        """
        tool = self.get_tool(name)
        if not tool:
            err = f"Unknown tool: '{name}'. Available: {list(self._tools.keys())}"
            logger.error(err)
            return {"success": False, "error": err, "tool": name, "exit_code": 1}

        start_time = time.time()
        logger.info(f"Executing tool '{name}' with arguments: {arguments}")

        try:
            # Map common argument name differences for compatibility
            mapped_args = dict(arguments)
            if "file_path" in tool.parameters.get("properties", {}) and "filepath" in mapped_args:
                mapped_args["file_path"] = mapped_args.pop("filepath")
            if "file_path" in tool.parameters.get("properties", {}) and "filename" in mapped_args and "file_path" not in mapped_args:
                mapped_args["file_path"] = mapped_args.pop("filename")

            validated_args = tool.validate_args(mapped_args)
            result = await tool.arun(**validated_args)
            duration = time.time() - start_time

            # Normalize result dict
            res_obj = result if isinstance(result, dict) else {"output": str(result), "success": True}
            success = res_obj.get("success", True)
            exit_code = res_obj.get("exit_code", 0 if success else 1)

            record = {
                "tool": name,
                "arguments": arguments,
                "duration_seconds": round(duration, 3),
                "timestamp": time.time(),
                "success": success,
                "exit_code": exit_code,
                "stdout": res_obj.get("stdout", ""),
                "stderr": res_obj.get("stderr", "")
            }
            self._execution_history.append(record)

            logger.info(f"Tool '{name}' completed in {duration:.3f}s (success={success})")
            return {
                "success": success,
                "tool": name,
                "duration_seconds": round(duration, 3),
                "exit_code": exit_code,
                "result": res_obj,
                "stdout": res_obj.get("stdout", ""),
                "stderr": res_obj.get("stderr", "")
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Execution error in tool '{name}': {e}", exc_info=True)
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

    def get_audit_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent tool execution audit trail."""
        return self._execution_history[-limit:]


# Global singleton instance
tool_manager = ToolManager()
