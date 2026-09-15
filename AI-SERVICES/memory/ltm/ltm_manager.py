"""
LTM Manager for Sovereign AI Workbench.
Coordinates persistent semantic memory and knowledge graph relationships.
"""

import os
from typing import Any, Dict, List, Optional
from core.config import settings
from core.logging import logger
from memory.models import MemoryItem
from memory.ltm.memory_retriever import memory_retriever
from memory.ltm.memory_writer import memory_writer
from memory.vector.qdrant_service import qdrant_service
from memory.graph.neo4j_service import neo4j_service
from memory.mem0.mem0_service import mem0_service


class LTMManager:
    """Enterprise coordinator for Long-Term Memory (LTM)."""

    def __init__(self, enabled: Optional[bool] = None):
        self.enabled = (
            enabled
            if enabled is not None
            else (os.getenv("LTM_ENABLED", "true").lower() == "true")
        )
        self.retriever = memory_retriever
        self.writer = memory_writer
        logger.info(f"[LTM] Initialized LTMManager (Enabled: {self.enabled})")

    async def health_check(self) -> Dict[str, Any]:
        """Check status of all LTM storage and indexing backends."""
        if not self.enabled:
            return {"status": "disabled"}

        qdrant_st = await qdrant_service.health_check()
        neo4j_st = await neo4j_service.health_check()
        mem0_st = await mem0_service.health_check()

        overall = "healthy"
        if qdrant_st.get("status") != "healthy" or neo4j_st.get("status") != "healthy":
            overall = "degraded"
        if qdrant_st.get("status") == "unavailable" and neo4j_st.get("status") == "unavailable":
            overall = "unavailable"

        return {
            "status": overall,
            "qdrant": qdrant_st,
            "neo4j": neo4j_st,
            "mem0": mem0_st
        }

    async def add_memory(
        self,
        user_id: str,
        content: str,
        conversation_id: Optional[str] = None,
        source_message_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        importance: float = 0.8
    ) -> Optional[MemoryItem]:
        """Store a persistent memory."""
        if not self.enabled:
            return None
        return await self.writer.write_memory(
            user_id=user_id,
            content=content,
            conversation_id=conversation_id,
            source_message_id=source_message_id,
            memory_type=memory_type,
            importance=importance
        )

    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories matching query."""
        if not self.enabled:
            return []
        return await self.retriever.retrieve_memories(
            query=query,
            user_id=user_id,
            limit=limit,
            score_threshold=score_threshold
        )

    async def get_context(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> str:
        """Build enriched prompt context from LTM vector and Neo4j graph."""
        if not self.enabled:
            return ""
        return await self.retriever.build_context_block(query=query, user_id=user_id)

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from Qdrant and Mem0."""
        q_del = await qdrant_service.delete_memory(memory_id)
        m_del = await mem0_service.delete_memory(memory_id)
        return q_del or m_del

    async def extract_from_dialog(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        conversation_id: Optional[str] = None,
        source_message_id: Optional[str] = None
    ):
        """Asynchronously extract and persist facts from conversation exchange."""
        if not self.enabled:
            return
        await self.writer.extract_and_store_from_dialog(
            user_id=user_id,
            user_message=user_message,
            assistant_response=assistant_response,
            conversation_id=conversation_id,
            source_message_id=source_message_id
        )


# Global singleton instance
ltm_manager = LTMManager()
