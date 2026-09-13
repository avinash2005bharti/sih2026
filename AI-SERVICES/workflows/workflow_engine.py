"""
Sovereign Workflow Engine.
Executes multi-step agentic workflows: step planning, tool execution via tool_manager,
failure retries, result aggregation, and sovereign audit trail tracking.
"""

import time
import json
import asyncio
from typing import Any, Dict, List, Optional, Callable
from tools.tool_manager import tool_manager
from core.logging import logger


class WorkflowStep:
    """Individual executable step in a workflow."""

    def __init__(
        self,
        name: str,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        action: Optional[Callable] = None,
        description: str = "",
        max_retries: int = 1
    ):
        self.name = name
        self.tool_name = tool_name
        self.arguments = arguments or {}
        self.action = action
        self.description = description
        self.max_retries = max_retries
        self.result: Optional[Dict[str, Any]] = None
        self.duration_seconds: float = 0.0
        self.success: bool = False
        self.error: Optional[str] = None


class WorkflowEngine:
    """Orchestrates structured task execution across tools and models."""

    def __init__(self):
        self._active_workflows: Dict[str, Any] = {}
        self._audit_log: List[Dict[str, Any]] = []

    async def execute_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a single workflow step with retry and error boundary."""
        start_time = time.time()
        logger.info(f"[WORKFLOW] Starting step '{step.name}' ({step.description})...")

        for attempt in range(step.max_retries + 1):
            try:
                if step.tool_name:
                    res = await tool_manager.execute_tool(step.tool_name, step.arguments)
                    step.duration_seconds = res.get("duration_seconds", round(time.time() - start_time, 3))
                    step.success = res.get("success", False)
                    step.result = res.get("result", res)
                    step.error = res.get("error")
                elif step.action:
                    res = await step.action(**step.arguments)
                    step.duration_seconds = round(time.time() - start_time, 3)
                    step.success = True
                    step.result = res
                else:
                    raise ValueError(f"Step '{step.name}' has no tool_name or action defined.")

                if step.success:
                    break
                else:
                    logger.warning(f"[WORKFLOW] Step '{step.name}' failed attempt {attempt + 1}: {step.error}")

            except Exception as e:
                step.duration_seconds = round(time.time() - start_time, 3)
                step.success = False
                step.error = str(e)
                logger.error(f"[WORKFLOW] Step '{step.name}' exception on attempt {attempt + 1}: {e}")

        # Record audit log
        audit_entry = {
            "step": step.name,
            "tool": step.tool_name,
            "arguments": step.arguments,
            "duration_seconds": step.duration_seconds,
            "success": step.success,
            "error": step.error,
            "timestamp": time.time()
        }
        self._audit_log.append(audit_entry)
        return audit_entry

    async def execute_pipeline(self, steps: List[WorkflowStep]) -> Dict[str, Any]:
        """Execute a sequence of dependent workflow steps."""
        start_time = time.time()
        results = []
        overall_success = True

        for step in steps:
            audit = await self.execute_step(step)
            results.append(audit)
            if not step.success:
                overall_success = False
                logger.warning(f"[WORKFLOW] Pipeline halted or degraded due to step failure: '{step.name}'")
                break

        total_duration = round(time.time() - start_time, 3)
        return {
            "success": overall_success,
            "total_duration_seconds": total_duration,
            "total_steps": len(steps),
            "executed_steps": len(results),
            "step_records": results
        }

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent workflow audit log."""
        return self._audit_log[-limit:]


# Global singleton engine
workflow_engine = WorkflowEngine()
