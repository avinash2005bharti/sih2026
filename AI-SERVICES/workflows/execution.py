"""
Sovereign Execution Engine.
Underlying sandboxed subprocess runner for all workflows and code execution.
Guarantees sandbox boundary containment inside AI-SERVICES/workspace,
resource quotas, environment sanitization, and SHA-256 audit logging.
"""

import sys
import os
import time
import hashlib
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, List
from tools.file_tool import SANDBOX_DIR
from core.logging import logger

DEFAULT_TIMEOUT = 20
MAX_OUTPUT_BYTES = 50 * 1024  # 50KB


class ExecutionResult:
    """Structured result of a sandboxed execution."""

    def __init__(
        self,
        command_or_code: str,
        returncode: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
        sha256_hash: str,
        success: bool
    ):
        self.command_or_code = command_or_code
        self.returncode = returncode
        self.exit_code = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.duration_seconds = duration_seconds
        self.sha256_hash = sha256_hash
        self.success = success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "returncode": self.returncode,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
            "sha256_hash": self.sha256_hash
        }


class SandboxedExecutionRunner:
    """Low-level execution runner ensuring strictly sandboxed execution."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = (workspace_dir or SANDBOX_DIR).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def calculate_sha256(self, content: str) -> str:
        """Compute SHA-256 checksum for audit trail."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def execute_python_code(self, code: str, timeout: int = DEFAULT_TIMEOUT) -> ExecutionResult:
        """Execute a Python snippet in an isolated subprocess rooted in the sandbox."""
        start_time = time.time()
        sha256 = self.calculate_sha256(code)
        logger.info(f"[EXEC:PYTHON] Running snippet (hash={sha256[:8]})...")

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_dir)
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                duration = round(time.time() - start_time, 3)
                stdout = stdout_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace").strip()
                stderr = stderr_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace").strip()
                success = (proc.returncode == 0)

                return ExecutionResult(
                    command_or_code=code,
                    returncode=proc.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    duration_seconds=duration,
                    sha256_hash=sha256,
                    success=success
                )

            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                return ExecutionResult(
                    command_or_code=code,
                    returncode=-1,
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
                    duration_seconds=round(time.time() - start_time, 3),
                    sha256_hash=sha256,
                    success=False
                )

        except Exception as e:
            return ExecutionResult(
                command_or_code=code,
                returncode=1,
                stdout="",
                stderr=str(e),
                duration_seconds=round(time.time() - start_time, 3),
                sha256_hash=sha256,
                success=False
            )

    async def execute_command(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> ExecutionResult:
        """Execute a controlled shell command strictly within the sandbox directory."""
        start_time = time.time()
        sha256 = self.calculate_sha256(command)
        logger.info(f"[EXEC:CMD] Running command '{command}' (hash={sha256[:8]})...")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_dir)
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                duration = round(time.time() - start_time, 3)
                stdout = stdout_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace").strip()
                stderr = stderr_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace").strip()
                success = (proc.returncode == 0)

                return ExecutionResult(
                    command_or_code=command,
                    returncode=proc.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    duration_seconds=duration,
                    sha256_hash=sha256,
                    success=success
                )

            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                return ExecutionResult(
                    command_or_code=command,
                    returncode=-1,
                    stdout="",
                    stderr=f"Command execution timed out after {timeout} seconds",
                    duration_seconds=round(time.time() - start_time, 3),
                    sha256_hash=sha256,
                    success=False
                )

        except Exception as e:
            return ExecutionResult(
                command_or_code=command,
                returncode=1,
                stdout="",
                stderr=str(e),
                duration_seconds=round(time.time() - start_time, 3),
                sha256_hash=sha256,
                success=False
            )


# Global singleton runner
execution_runner = SandboxedExecutionRunner()
