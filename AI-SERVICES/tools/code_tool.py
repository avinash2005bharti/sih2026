"""
Sandboxed code execution and command tools for Sovereign AI Workbench.
Executes Python scripts and controlled shell commands strictly within the sovereign sandbox.
Enforces timeouts, allowlists, output size limits, and security guardrails.
"""

import sys
import time
import asyncio
import shlex
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, List
from tools.base_tool import BaseTool
from tools.file_tool import SANDBOX_DIR
from core.logging import logger

MAX_TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 10000

# High-risk patterns blocked from python scripts
DISALLOWED_PATTERNS = [
    "os.system",
    "shutil.rmtree",
    "subprocess.Popen",
    "subprocess.call",
    "ctypes",
    "__import__('os').system",
    ":(){ :|:& };:",  # fork bomb
]

# Allowlist for controlled terminal commands
ALLOWED_COMMAND_BINARIES = {
    "python", "python3", "ls", "dir", "cat", "type", "echo",
    "find", "grep", "pwd", "date", "whoami", "git", "head", "tail", "wc"
}

DISALLOWED_COMMAND_TOKENS = [
    "sudo", "rm -rf", "mkfs", "dd if=", "chmod", "chown", "curl", "wget",
    "> /dev/", "nc -", "/etc/", "powershell -enc"
]


class PythonExecutionTool(BaseTool):
    """Executes Python code safely in a subprocess rooted in the sandbox."""

    name = "execute_python"
    description = (
        "Execute a Python script safely within the sovereign workspace sandbox. "
        "Useful for data analysis, calculations, generating charts/data, and automated verification."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python source code to execute"
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Maximum execution time in seconds (1 to 30, default 15)"
            }
        },
        "required": ["code"]
    }

    async def arun(self, code: str, timeout_seconds: int = 15, **kwargs) -> Dict[str, Any]:
        timeout = max(1, min(timeout_seconds, MAX_TIMEOUT_SECONDS))

        for pattern in DISALLOWED_PATTERNS:
            if pattern in code:
                logger.warning(f"PythonExecutionTool blocked code containing forbidden pattern: {pattern}")
                return {
                    "success": False,
                    "error": f"Security policy violation: Code contains restricted pattern '{pattern}'"
                }

        script_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="sovereign_exec_",
                dir=str(SANDBOX_DIR),
                delete=False,
                encoding="utf-8"
            ) as tmp:
                tmp.write(code)
                script_path = Path(tmp.name)

            start_time = time.time()

            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(SANDBOX_DIR)
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                duration = time.time() - start_time

                stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
                stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

                if len(stdout) > MAX_OUTPUT_CHARS:
                    stdout = stdout[:MAX_OUTPUT_CHARS] + f"\n... [Output truncated at {MAX_OUTPUT_CHARS} characters]"
                if len(stderr) > MAX_OUTPUT_CHARS:
                    stderr = stderr[:MAX_OUTPUT_CHARS] + f"\n... [Stderr truncated at {MAX_OUTPUT_CHARS} characters]"

                success = (proc.returncode == 0)
                logger.info(f"PythonExecutionTool completed (rc={proc.returncode}, duration={duration:.2f}s)")

                return {
                    "success": success,
                    "returncode": proc.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": proc.returncode,
                    "duration_seconds": round(duration, 3)
                }

            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                logger.warning(f"PythonExecutionTool timed out after {timeout}s")
                return {
                    "success": False,
                    "error": f"Execution timed out after {timeout} seconds",
                    "returncode": -1,
                    "exit_code": -1
                }

        except Exception as e:
            logger.error(f"PythonExecutionTool error: {e}")
            return {"success": False, "error": str(e), "exit_code": -1}

        finally:
            if script_path and script_path.exists():
                try:
                    script_path.unlink()
                except Exception:
                    pass


class ControlledCommandTool(BaseTool):
    """Executes safe, allowed system and terminal commands strictly inside the workspace sandbox."""

    name = "execute_command"
    description = (
        "Execute a safe terminal command strictly inside the workspace sandbox directory. "
        "Allowed binaries: python, ls, dir, cat, type, echo, find, grep, pwd, date, whoami, git."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command line to execute inside the sandbox (e.g. 'python script.py', 'ls -la', 'dir')"
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Maximum execution time in seconds (default 15)"
            }
        },
        "required": ["command"]
    }

    async def arun(self, command: str, timeout_seconds: int = 15, **kwargs) -> Dict[str, Any]:
        cmd_str = command.strip()
        if not cmd_str:
            return {"success": False, "error": "Command string cannot be empty", "exit_code": -1}

        # Guard against path escaping or destructive tokens
        cmd_lower = cmd_str.lower()
        for token in DISALLOWED_COMMAND_TOKENS:
            if token in cmd_lower:
                logger.warning(f"ControlledCommandTool blocked command containing forbidden token: '{token}'")
                return {
                    "success": False,
                    "error": f"Security policy violation: Command contains restricted token '{token}'",
                    "exit_code": -1
                }

        # Check binary allowlist
        try:
            tokens = shlex.split(cmd_str)
        except Exception:
            tokens = cmd_str.split()

        binary = Path(tokens[0]).name.lower()
        if binary not in ALLOWED_COMMAND_BINARIES and not binary.endswith(".py"):
            logger.warning(f"ControlledCommandTool blocked non-whitelisted binary: '{binary}'")
            return {
                "success": False,
                "error": f"Security policy violation: Binary '{binary}' is not permitted. Allowed: {sorted(list(ALLOWED_COMMAND_BINARIES))}",
                "exit_code": -1
            }

        timeout = max(1, min(timeout_seconds, MAX_TIMEOUT_SECONDS))
        start_time = time.time()

        try:
            # Run within SANDBOX_DIR
            proc = await asyncio.create_subprocess_shell(
                cmd_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(SANDBOX_DIR)
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                duration = time.time() - start_time

                stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
                stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

                if len(stdout) > MAX_OUTPUT_CHARS:
                    stdout = stdout[:MAX_OUTPUT_CHARS] + f"\n... [Output truncated at {MAX_OUTPUT_CHARS} characters]"
                if len(stderr) > MAX_OUTPUT_CHARS:
                    stderr = stderr[:MAX_OUTPUT_CHARS] + f"\n... [Stderr truncated at {MAX_OUTPUT_CHARS} characters]"

                success = (proc.returncode == 0)
                logger.info(f"ControlledCommandTool ran '{cmd_str}' (rc={proc.returncode}, {duration:.2f}s)")

                return {
                    "success": success,
                    "command": cmd_str,
                    "returncode": proc.returncode,
                    "exit_code": proc.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "duration_seconds": round(duration, 3)
                }

            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "exit_code": -1
                }

        except Exception as e:
            logger.error(f"ControlledCommandTool execution error: {e}")
            return {"success": False, "error": str(e), "exit_code": -1}
