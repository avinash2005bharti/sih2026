"""
Pydantic models and schemas for the Sovereign Local Memory Architecture.
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    INSTRUCTION = "instruction"
    PROJECT_KNOWLEDGE = "project_knowledge"
    TECHNICAL_KNOWLEDGE = "technical_knowledge"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    TASK_CONTEXT = "task_context"


class MemoryItem(BaseModel):
    """Schema for a single persistent memory item stored in Qdrant & Neo4j."""
    memory_id: str
    user_id: str
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    project_id: Optional[str] = None
    memory_type: str = Field(default=MemoryType.FACT.value)
    content: str
    source: str = "conversation"
    source_id: Optional[str] = None
    source_message_id: Optional[str] = None
    importance: float = 0.8
    confidence: float = 0.95
    entity_references: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class STMMessage(BaseModel):
    """Schema for a short-term message in active conversation context."""
    role: str  # "user", "assistant", "system", "agent"
    content: str
    message_id: Optional[str] = None
    agent_id: Optional[str] = None
    created_at: Optional[Any] = None


class STMContext(BaseModel):
    """Schema for STM active conversation context."""
    conversation_id: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    messages: List[STMMessage] = Field(default_factory=list)
    summary: Optional[str] = None
    estimated_tokens: int = 0


class MemorySearchRequest(BaseModel):
    """Request payload for semantic memory search."""
    query: str
    user_id: Optional[str] = None
    limit: int = 5
    score_threshold: Optional[float] = 0.65
    memory_type: Optional[str] = None


class MemoryCreateRequest(BaseModel):
    """Request payload to manually record a memory."""
    content: str
    user_id: str
    memory_type: Optional[str] = "fact"
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    importance: Optional[float] = 0.8
    metadata: Optional[Dict[str, Any]] = None


class MemoryHealthStatus(BaseModel):
    """Schema for unified memory system health check."""
    memory: str
    stm: str
    ltm: str
    qdrant: str
    neo4j: str
    mem0: str
    ollama: str
    embedding_model: str
    details: Dict[str, Any] = Field(default_factory=dict)
