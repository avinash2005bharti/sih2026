"""
Central LangChain Tool Registry for Sovereign AI Workbench.
All tools execute safely within the workspace sandbox: AI-SERVICES/workspace.
Enforces boundaries, path traversal prevention, and structured observations.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from langchain_core.tools import tool
from core.logging import logger

BASE_DIR = Path(__file__).resolve().parent.parent
SANDBOX_DIR = (BASE_DIR / "workspace").resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = (SANDBOX_DIR / "reports").resolve()
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_safe_path(filepath: str) -> Path:
    """
    Resolve and validate a file path to guarantee it resides strictly inside SANDBOX_DIR.
    Prevents directory traversal attacks.
    """
    cleaned = filepath.replace("\\", "/").strip().lstrip("/")
    target = (SANDBOX_DIR / cleaned).resolve()
    try:
        if not target.is_relative_to(SANDBOX_DIR):
            raise PermissionError(f"Access denied: Path '{filepath}' attempts to escape sovereign sandbox.")
    except AttributeError:
        if not str(target).startswith(str(SANDBOX_DIR)):
            raise PermissionError(f"Access denied: Path '{filepath}' attempts to escape sovereign sandbox.")
    return target


@tool
def create_directory(dir_path: str) -> str:
    """
    Create a new directory or folder inside the sovereign workspace sandbox.
    Example: create_directory(dir_path="demo-project")
    """
    try:
        target = resolve_safe_path(dir_path)
        target.mkdir(parents=True, exist_ok=True)
        rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
        logger.info(f"[TOOL:create_directory] Created directory '{rel_path}'")
        return json.dumps({
            "success": True,
            "dir_path": rel_path,
            "message": f"Directory '{rel_path}' created successfully."
        })
    except Exception as e:
        logger.error(f"[TOOL:create_directory] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def create_file(file_path: str, content: str) -> str:
    """
    Create or overwrite a file with the specified text content inside the workspace sandbox.
    Example: create_file(file_path="demo-project/README.md", content="# Project Title\\nDescription here")
    """
    try:
        target = resolve_safe_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        bytes_written = len(content.encode("utf-8"))
        rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
        logger.info(f"[TOOL:create_file] Created file '{rel_path}' ({bytes_written} bytes)")
        return json.dumps({
            "success": True,
            "file_path": rel_path,
            "bytes_written": bytes_written,
            "message": f"File '{rel_path}' created successfully."
        })
    except Exception as e:
        logger.error(f"[TOOL:create_file] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def read_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """
    Read text contents from a file inside the sovereign workspace sandbox.
    Example: read_file(file_path="data.csv")
    """
    try:
        target = resolve_safe_path(file_path)
        if not target.exists():
            return json.dumps({"success": False, "error": f"File not found: {file_path}"})
        if not target.is_file():
            return json.dumps({"success": False, "error": f"Path is not a regular file: {file_path}"})
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total_lines = len(lines)
        s = max(1, start_line) if start_line else 1
        e = min(total_lines, end_line) if end_line else total_lines
        content = "".join(lines[s - 1:e])
        logger.info(f"[TOOL:read_file] Read {len(content)} chars from '{file_path}'")
        return json.dumps({
            "success": True,
            "file_path": file_path,
            "total_lines": total_lines,
            "content": content
        })
    except Exception as e:
        logger.error(f"[TOOL:read_file] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def list_files(dir_path: str = ".") -> str:
    """
    List files and folders inside a given workspace directory.
    Example: list_files(dir_path=".")
    """
    try:
        target = resolve_safe_path(dir_path)
        if not target.exists():
            return json.dumps({"success": False, "error": f"Directory not found: {dir_path}"})
        if not target.is_dir():
            return json.dumps({"success": False, "error": f"Path is not a directory: {dir_path}"})
        entries = []
        for item in sorted(target.iterdir()):
            entries.append({
                "name": item.name,
                "path": str(item.relative_to(SANDBOX_DIR)).replace("\\", "/"),
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0
            })
        logger.info(f"[TOOL:list_files] Listed {len(entries)} items in '{dir_path}'")
        return json.dumps({
            "success": True,
            "dir_path": dir_path,
            "count": len(entries),
            "entries": entries
        })
    except Exception as e:
        logger.error(f"[TOOL:list_files] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def execute_python(code: str, timeout_seconds: int = 30) -> str:
    """
    Execute Python code in an isolated subprocess within the sovereign sandbox.
    Returns structured execution observations including stdout, stderr, and exit code.
    Example: execute_python(code="import math\\nprint(math.factorial(10))")
    """
    timeout = max(1, min(timeout_seconds, 60))
    logger.info(f"[TOOL:execute_python] Running python code ({len(code)} chars)...")
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(SANDBOX_DIR),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        success = (proc.returncode == 0)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        logger.info(f"[TOOL:execute_python] Completed (exit_code={proc.returncode})")
        return json.dumps({
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode
        })
    except subprocess.TimeoutExpired:
        logger.warning(f"[TOOL:execute_python] Execution timed out after {timeout}s")
        return json.dumps({"success": False, "error": f"Execution timed out after {timeout} seconds", "exit_code": -1})
    except Exception as e:
        logger.error(f"[TOOL:execute_python] Execution error: {e}")
        return json.dumps({"success": False, "error": str(e), "exit_code": -1})


@tool
def execute_code(code: str, language: str = "python") -> str:
    """
    Execute code in a supported programming language (default: python).
    Example: execute_code(code="print(12345 * 6789)", language="python")
    """
    if language.lower() in ["python", "py"]:
        return execute_python.invoke({"code": code})
    return json.dumps({
        "success": False,
        "error": f"Unsupported language '{language}'. Only 'python' is supported in the sovereign sandbox."
    })


@tool
def create_pdf(file_name: str, title: str, content: str) -> str:
    """
    Generate a real PDF document inside the sovereign workspace under reports/ using ReportLab.
    Example: create_pdf(file_name="architecture.pdf", title="Sovereign AI Architecture", content="This document outlines the on-premise architecture...")
    """
    if not file_name.endswith(".pdf"):
        file_name += ".pdf"
    
    # Strip path separators to ensure it stays in reports directory
    clean_name = Path(file_name).name
    target = REPORTS_DIR / clean_name

    logger.info(f"[TOOL:create_pdf] Generating PDF '{clean_name}' at {target}...")
    try:
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(str(target), pagesize=letter)
        story = [
            Paragraph(title, styles['Title']),
            Spacer(1, 14),
        ]
        for para in content.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip().replace("\n", "<br/>"), styles['Normal']))
                story.append(Spacer(1, 10))
        doc.build(story)

        if not target.exists():
            raise FileNotFoundError(f"PDF generation failed; file '{clean_name}' does not exist on disk.")

        size = target.stat().st_size
        rel_path = f"reports/{clean_name}"
        logger.info(f"[TOOL:create_pdf] PDF successfully generated! Size: {size} bytes")
        return json.dumps({
            "success": True,
            "file_name": clean_name,
            "file_path": rel_path,
            "size_bytes": size,
            "mime_type": "application/pdf",
            "message": f"PDF '{clean_name}' generated successfully ({size} bytes)."
        })
    except Exception as e:
        logger.error(f"[TOOL:create_pdf] PDF generation error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def execute_command(command: str) -> str:
    """
    Execute a safe terminal command strictly inside the workspace sandbox directory.
    Allowed commands: python, ls, dir, cat, type, echo, find, grep, pwd, date, whoami, git.
    Example: execute_command(command="python test.py")
    """
    try:
        from tools.tool_manager import tool_manager
        import asyncio
        res = asyncio.run(tool_manager.execute_tool("execute_command", {"command": command}))
        return json.dumps(res.get("result", res))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "exit_code": 1})


# Canonical list of registered tools
AGENT_TOOLS = [
    create_directory,
    create_file,
    read_file,
    list_files,
    execute_python,
    execute_code,
    execute_command,
    create_pdf,
]

# Map both canonical names and dot-notation aliases
TOOLS_MAP: Dict[str, Any] = {
    # Canonical names
    "create_directory": create_directory,
    "create_file": create_file,
    "read_file": read_file,
    "list_files": list_files,
    "execute_python": execute_python,
    "execute_code": execute_code,
    "execute_command": execute_command,
    "create_pdf": create_pdf,
    # Dot-notation aliases
    "file.create_directory": create_directory,
    "file.create": create_file,
    "file.read": read_file,
    "file.list": list_files,
    "python.execute": execute_python,
    "code.execute": execute_code,
    "command.execute": execute_command,
    "pdf.create": create_pdf,
}


def get_agent_tools() -> List[Any]:
    """Retrieve all LangChain compatible tools for agent binding."""
    return list(AGENT_TOOLS)


def resolve_tool(name: str) -> Optional[Any]:
    """Resolve a tool by canonical name or alias."""
    return TOOLS_MAP.get(name)
