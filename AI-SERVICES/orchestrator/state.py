"""
State schemas for the Sovereign Agentic Orchestrator.
Maintains state transitions across Planner, Router, Agent Selector,
Executor, Tools, Verifier, and Finalizer nodes.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepPlan(BaseModel):
    """A single discrete step in the agentic execution plan."""
    step_number: int
    title: str
    description: str
    target_agent: str = "general"
    required_tools: List[str] = Field(default_factory=list)
    expected_outcome: str = ""
    status: str = "pending"  # pending, in_progress, completed, failed


class Observation(BaseModel):
    """The result or finding produced by executing a step or tool."""
    step_number: int
    agent_name: str
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    success: bool = True
    thought: str = ""
    timestamp: float = Field(default_factory=time.time)


class AgenticState(BaseModel):
    """The complete orchestrator state carried across all graph nodes."""
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    user_query: str
    conversation_id: Optional[str] = None
    route: str = "auto"  # direct, agentic, coding, vision, doc_analysis
    is_direct_chat: bool = False

    plan: List[StepPlan] = Field(default_factory=list)
    current_step_index: int = 0

    selected_agent: str = "general"
    selected_model: str = "qwen2.5-coder:3b"

    observations: List[Observation] = Field(default_factory=list)
    verification_passed: bool = False
    verification_notes: str = ""
    retry_count: int = 0
    max_retries: int = 2

    iteration: int = 0
    max_iterations: int = 12

    final_response: str = ""
    citations: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    status: str = "initialized"  # initialized, routing, planning, executing, verifying, finalizing, completed, error

    class Config:
        arbitrary_types_allowed = True
