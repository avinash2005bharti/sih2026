"""
State schemas for the Sovereign Agentic Orchestrator.
Maintains state transitions across Planner, Router, Agent Selector,
Executor, Tools, Verifier, and Finalizer nodes.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TaskContract(BaseModel):
    """Formal contract outlining the task objective, constraints, and criteria."""
    objective: str = ""
    required_outputs: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PlanStep(BaseModel):
    """A discrete step in the agentic DAG execution plan."""
    id: int = 1
    step_number: int = 1
    title: str = ""
    description: str = ""
    agent: str = "general"
    target_agent: str = "general"
    tool: Optional[str] = None
    required_tools: List[str] = Field(default_factory=list)
    dependencies: List[int] = Field(default_factory=list)
    model: Optional[str] = None
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED, RETRYING
    expected_output: str = ""
    expected_outcome: str = ""
    error: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if "step_number" in data and "id" not in data:
            self.id = data["step_number"]
        elif "id" in data and "step_number" not in data:
            self.step_number = data["id"]
        if "target_agent" in data and "agent" not in data:
            self.agent = data["target_agent"]
        elif "agent" in data and "target_agent" not in data:
            self.target_agent = data["agent"]

    model_config = ConfigDict(arbitrary_types_allowed=True)


StepPlan = PlanStep


class Observation(BaseModel):
    """The result or finding produced by executing a step or tool."""
    step_number: int = 1
    agent_name: str = "general"
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    success: bool = True
    thought: str = ""
    timestamp: float = Field(default_factory=time.time)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ValidationVerdict(BaseModel):
    """Artifact or execution verification result."""
    valid: bool = True
    score: int = 100
    issues: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    corrections: List[str] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgenticState(BaseModel):
    """The complete orchestrator state carried across all graph nodes."""
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    user_query: str = ""
    user_request: str = ""
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    user_role: str = "engineer"

    route: str = "auto"
    is_direct_chat: bool = False
    is_complex_task: bool = False

    task_contract: TaskContract = Field(default_factory=TaskContract)
    plan: List[PlanStep] = Field(default_factory=list)
    plan_valid: bool = True
    plan_issues: List[str] = Field(default_factory=list)
    current_step_index: int = 0

    selected_agent: str = "general"
    selected_model: str = "qwen2.5:1.5b"

    observations: List[Observation] = Field(default_factory=list)
    validation_verdict: ValidationVerdict = Field(default_factory=ValidationVerdict)
    verification_passed: bool = False
    verification_notes: str = ""
    retry_count: int = 0
    max_retries: int = 2

    iteration: int = 0
    max_iterations: int = 12

    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning_traces: List[Dict[str, Any]] = Field(default_factory=list)
    final_response: str = ""
    citations: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    status: str = "initialized"

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data):
        super().__init__(**data)
        if self.user_query and not self.user_request:
            self.user_request = self.user_query
        elif self.user_request and not self.user_query:
            self.user_query = self.user_request

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


OrchestratorState = AgenticState
WorkbenchState = AgenticState

