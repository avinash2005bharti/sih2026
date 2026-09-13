"""
Sandboxed file system tools for Sovereign AI Workbench.
Strictly enforces sandboxed boundaries inside AI-SERVICES/workspace to prevent path traversal and arbitrary disk access.
"""

import os
import shutil
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional
from tools.base_tool import BaseTool
from core.logging import logger

# Sandbox root directory: sih2026-main
BASE_DIR = Path(__file__).resolve().parent.parent
SANDBOX_DIR = BASE_DIR.parent.resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_safe_path(filepath: str) -> Path:
    """
    Resolve and validate a file path to guarantee it resides strictly inside SANDBOX_DIR.
    Prevents path traversal attacks (e.g., ../../../etc/passwd).
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


class ReadFileTool(BaseTool):
    """Safely reads content from a file inside the sandbox."""

    name = "read_file"
    description = "Read the contents of a file inside the sovereign workspace sandbox."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to the file inside the workspace (e.g. 'notes.txt', 'data/report.csv')"
            },
            "start_line": {
                "type": "integer",
                "description": "Optional 1-indexed start line number to read from"
            },
            "end_line": {
                "type": "integer",
                "description": "Optional 1-indexed end line number to read up to"
            }
        },
        "required": ["file_path"]
    }

    async def arun(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(file_path)
            if not target.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            if not target.is_file():
                return {"success": False, "error": f"Path is not a regular file: {file_path}"}

            size = target.stat().st_size
            if size > 5 * 1024 * 1024:  # 5MB limit
                return {"success": False, "error": f"File exceeds maximum allowed read size of 5MB (size: {size} bytes)"}

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            s = max(1, start_line) if start_line else 1
            e = min(total_lines, end_line) if end_line else total_lines

            sliced_lines = lines[s - 1:e]
            content = "".join(sliced_lines)

            logger.info(f"ReadFileTool read {len(sliced_lines)} lines from {file_path}")
            return {
                "success": True,
                "file_path": file_path,
                "total_lines": total_lines,
                "range": [s, e],
                "content": content
            }
        except PermissionError as pe:
            logger.warning(f"ReadFileTool permission error: {pe}")
            return {"success": False, "error": str(pe)}
        except Exception as e:
            logger.error(f"ReadFileTool failed on {file_path}: {e}")
            return {"success": False, "error": str(e)}


class WriteFileTool(BaseTool):
    """Safely writes or appends content to a file inside the sandbox."""

    name = "write_file"
    description = "Create or overwrite a file in the workspace sandbox with given content."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to target file (e.g. 'output/summary.md')"
            },
            "content": {
                "type": "string",
                "description": "Text content to write into the file"
            },
            "append": {
                "type": "boolean",
                "description": "If true, appends content to the end of the file instead of overwriting"
            }
        },
        "required": ["file_path", "content"]
    }

    async def arun(self, file_path: str, content: str, append: bool = False, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            mode = "a" if append else "w"
            with open(target, mode, encoding="utf-8") as f:
                f.write(content)

            bytes_written = len(content.encode("utf-8"))
            logger.info(f"WriteFileTool wrote {bytes_written} bytes to {file_path}")
            return {
                "success": True,
                "file_path": file_path,
                "bytes_written": bytes_written,
                "mode": "appended" if append else "overwritten"
            }
        except PermissionError as pe:
            return {"success": False, "error": str(pe)}
        except Exception as e:
            logger.error(f"WriteFileTool failed on {file_path}: {e}")
            return {"success": False, "error": str(e)}


class CreateDirectoryTool(BaseTool):
    """Safely creates a new folder/directory inside the sandbox."""

    name = "create_directory"
    description = "Create a new directory or folder inside the sovereign workspace sandbox."
    parameters = {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Relative folder path inside workspace (e.g. 'reports', 'project/src')"
            }
        },
        "required": ["dir_path"]
    }

    async def arun(self, dir_path: str, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(dir_path)
            target.mkdir(parents=True, exist_ok=True)
            rel = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
            return {"success": True, "dir_path": rel, "message": f"Directory '{rel}' created successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}


class DeleteFileTool(BaseTool):
    """Safely deletes a file inside the sandbox."""

    name = "delete_file"
    description = "Delete a file inside the sovereign workspace sandbox."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to the file to delete"
            }
        },
        "required": ["file_path"]
    }

    async def arun(self, file_path: str, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(file_path)
            if not target.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            if target.is_dir():
                return {"success": False, "error": f"Cannot delete directory with delete_file: {file_path}"}

            target.unlink()
            logger.info(f"DeleteFileTool deleted file {file_path}")
            return {"success": True, "file_path": file_path, "message": f"File '{file_path}' deleted."}
        except Exception as e:
            return {"success": False, "error": str(e)}


class MoveFileTool(BaseTool):
    """Moves or renames a file inside the sandbox."""

    name = "move_file"
    description = "Move or rename a file within the sovereign workspace sandbox."
    parameters = {
        "type": "object",
        "properties": {
            "source_path": {
                "type": "string",
                "description": "Relative path of existing file"
            },
            "destination_path": {
                "type": "string",
                "description": "Relative path of new destination file"
            }
        },
        "required": ["source_path", "destination_path"]
    }

    async def arun(self, source_path: str, destination_path: str, **kwargs) -> Dict[str, Any]:
        try:
            src = _resolve_safe_path(source_path)
            dst = _resolve_safe_path(destination_path)
            if not src.exists():
                return {"success": False, "error": f"Source file not found: {source_path}"}

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return {"success": True, "source": source_path, "destination": destination_path}
        except Exception as e:
            return {"success": False, "error": str(e)}


class PatchFileTool(BaseTool):
    """Applies targeted string replacement to a file in the sandbox and generates a diff."""

    name = "patch_file"
    description = "Replace target text in an existing file with new text and return a diff of changes."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path to file inside workspace"
            },
            "target_text": {
                "type": "string",
                "description": "Exact text to find and replace"
            },
            "replacement_text": {
                "type": "string",
                "description": "Replacement text"
            }
        },
        "required": ["file_path", "target_text", "replacement_text"]
    }

    async def arun(self, file_path: str, target_text: str, replacement_text: str, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(file_path)
            if not target.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            with open(target, "r", encoding="utf-8") as f:
                original = f.read()

            if target_text not in original:
                return {"success": False, "error": f"Target text not found in {file_path}"}

            updated = original.replace(target_text, replacement_text, 1)

            # Generate diff
            diff = list(difflib.unified_diff(
                original.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}"
            ))

            with open(target, "w", encoding="utf-8") as f:
                f.write(updated)

            return {
                "success": True,
                "file_path": file_path,
                "diff": "".join(diff),
                "message": f"Successfully patched {file_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ListDirectoryTool(BaseTool):
    """Lists files and directories inside the sandbox."""

    name = "list_directory"
    description = "List files and folders inside a given workspace directory."
    parameters = {
        "type": "object",
        "properties": {
            "dir_path": {
                "type": "string",
                "description": "Relative folder path inside workspace (use '.' for workspace root)"
            }
        },
        "required": ["dir_path"]
    }

    async def arun(self, dir_path: str = ".", **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(dir_path)
            if not target.exists():
                return {"success": False, "error": f"Directory not found: {dir_path}"}
            if not target.is_dir():
                return {"success": False, "error": f"Path is not a directory: {dir_path}"}

            entries = []
            for item in sorted(target.iterdir()):
                rel = item.relative_to(SANDBOX_DIR)
                entries.append({
                    "name": item.name,
                    "path": str(rel).replace("\\", "/"),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0
                })

            return {"success": True, "dir_path": dir_path, "count": len(entries), "entries": entries}
        except PermissionError as pe:
            return {"success": False, "error": str(pe)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class FileDiffTool(BaseTool):
    """Generates unified diff between original and proposed content."""

    name = "file_diff"
    description = "Compare existing file content with new content and output a unified diff."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative file path inside workspace"
            },
            "new_content": {
                "type": "string",
                "description": "New content to compare against existing file"
            }
        },
        "required": ["file_path", "new_content"]
    }

    async def arun(self, file_path: str, new_content: str, **kwargs) -> Dict[str, Any]:
        try:
            target = _resolve_safe_path(file_path)
            if not target.exists():
                old_lines = []
            else:
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    old_lines = f.readlines()

            new_lines = new_content.splitlines(keepends=True)
            diff = list(difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}"
            ))

            return {
                "success": True,
                "file_path": file_path,
                "has_changes": len(diff) > 0,
                "diff": "".join(diff)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
