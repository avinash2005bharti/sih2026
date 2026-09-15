from pydantic import BaseModel, Field
from typing import List, Optional, Any

class AgentExecutionState(BaseModel):
    """Execution state stored in MongoDB to track execution lifecycle."""
    execution_id: str
    conversation_id: str
    user_request: str

    current_agent: Optional[str] = None
    current_model: Optional[str] = None

    plan: List[Any] = Field(default_factory=list)
    completed_steps: List[Any] = Field(default_factory=list)
    pending_steps: List[Any] = Field(default_factory=list)

    tool_calls: List[Any] = Field(default_factory=list)
    tool_results: List[Any] = Field(default_factory=list)

    memories: List[Any] = Field(default_factory=list)
    retrieved_documents: List[Any] = Field(default_factory=list)

    artifacts: List[Any] = Field(default_factory=list)

    status: str = "started"
    error: Optional[str] = None
