"""
API routes for autonomous Agentic Task Execution.
Allows running complex multi-step workflows via SovereignOrchestrator.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from orchestrator.graph import orchestrator
from orchestrator.state import AgenticState
from core.logging import logger

router = APIRouter(prefix="/api")

# Memory store for recent task execution states
_TASK_STORE: Dict[str, Dict[str, Any]] = {}


class ExecuteTaskRequest(BaseModel):
    objective: str = Field(..., min_length=2, description="Task objective or instruction")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    selected_agents: Optional[List[str]] = Field(None, description="Optional specialist agents requested")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional task parameters")


class TaskStepResponse(BaseModel):
    step_number: int
    title: str
    target_agent: str
    status: str
    expected_outcome: str


class ExecuteTaskResponse(BaseModel):
    task_id: str
    status: str
    route: str
    steps_total: int
    steps_completed: int
    plan: List[Dict[str, Any]]
    observations: List[Dict[str, Any]]
    final_response: str


@router.post("/tasks/execute", response_model=ExecuteTaskResponse, summary="Execute autonomous agentic task")
async def execute_task(request: ExecuteTaskRequest):
    """
    Execute a complex multi-step industrial workflow through the Sovereign Orchestrator:
    Planner -> Router -> Agent Selector -> Executor -> Tools -> Observation -> Verifier -> Finalizer.
    """
    try:
        logger.info(f"Task execution request received: '{request.objective[:80]}...'")

        # Run sovereign orchestrator state graph
        state: AgenticState = await orchestrator.run(
            query=request.objective,
            conversation_id=request.conversation_id
        )

        # Format plan and observations for response
        formatted_plan = [p.dict() for p in state.plan]
        formatted_obs = [o.dict() for o in state.observations]

        response_data = {
            "task_id": state.task_id,
            "status": state.status,
            "route": state.route,
            "steps_total": len(state.plan),
            "steps_completed": state.current_step_index,
            "plan": formatted_plan,
            "observations": formatted_obs,
            "final_response": state.final_response
        }

        # Store in local task store
        _TASK_STORE[state.task_id] = response_data

        logger.info(f"Task '{state.task_id}' finished with status '{state.status}'")
        return ExecuteTaskResponse(**response_data)

    except Exception as e:
        logger.error(f"Task execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Task execution error: {str(e)}")


@router.get("/tasks/{task_id}", summary="Get task execution status and audit trace")
async def get_task(task_id: str):
    """Retrieve details, execution plan, observations, and result of a previously executed task."""
    if task_id not in _TASK_STORE:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return _TASK_STORE[task_id]


@router.get("/tasks", summary="List recent task executions")
async def list_tasks(limit: int = 20):
    """List recent executed tasks with status summaries."""
    recent = list(_TASK_STORE.values())[-limit:]
    return {"tasks": recent, "count": len(recent)}
