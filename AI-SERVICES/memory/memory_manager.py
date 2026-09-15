"""
Unified Memory Manager for Sovereign AI Workbench.
Centralizes access to:
1. STM (Short-Term Memory): Sliding window of active conversation messages (MongoDB / in-memory).
2. LTM (Long-Term Memory): Semantic vector retrieval and extraction (Mem0 / Qdrant).
3. Knowledge Graph: Relationship modeling, task provenance, and entity associations (Neo4j).
4. Local Embeddings: Ollama nomic-embed-text for 100% private vector operations.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from core.config import settings
from core.logging import logger
from memory.models import MemoryHealthStatus, MemoryItem, STMContext
from memory.stm.stm_manager import stm_manager
from memory.stm.context_builder import context_builder
from memory.ltm.ltm_manager import ltm_manager
from memory.embeddings.embedding_service import embedding_service
from memory.vector.qdrant_service import qdrant_service
from memory.graph.neo4j_service import neo4j_service
from memory.mem0.mem0_service import mem0_service


class MemoryManager:
    """Enterprise coordinator for all agentic memory operations."""

    def __init__(self):
        self.stm = stm_manager
        self.ltm = ltm_manager
        self.embeddings = embedding_service
        self.qdrant = qdrant_service
        self.graph = neo4j_service
        self.mem0 = mem0_service
        self.enabled = (os.getenv("MEMORY_ENABLED", "true").lower() == "true")
        logger.info(f"[MEMORY] Initialized MemoryManager (Master Enabled: {self.enabled})")

    # -------------------------------------------------------------------------
    # Context Retrieval (Read Flow before LLM)
    # -------------------------------------------------------------------------
    async def get_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> str:
        """
        Build complete unified memory context for LLM prompts:
        [STM Recent Dialog] + [LTM Recalled Facts & Preferences] + [Neo4j Graph Insights]
        """
        if not self.enabled:
            return ""

        context_parts = []

        # 1. STM Conversation Context
        if conversation_id:
            try:
                stm_ctx = await self.stm.get_conversation_context(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    agent_id=agent_id
                )
                formatted_stm = context_builder.format_history_for_prompt(stm_ctx, current_query=query)
                if formatted_stm:
                    context_parts.append(formatted_stm)
            except Exception as e:
                logger.debug(f"[MEMORY] STM context formatting warning: {e}")

        # 2. LTM Semantic Facts & Graph Relations
        try:
            ltm_context = await self.ltm.get_context(query=query, user_id=user_id)
            if ltm_context:
                context_parts.append(ltm_context)
        except Exception as e:
            logger.debug(f"[MEMORY] LTM context retrieval warning: {e}")

        return "\n\n".join(context_parts) if context_parts else ""

    async def build_enriched_context(self, user_id: str, query: str) -> str:
        """Backward-compatible helper for legacy callers."""
        return await self.get_context(query=query, user_id=user_id)

    # -------------------------------------------------------------------------
    # Memory Writing & Extraction (Write Flow after LLM)
    # -------------------------------------------------------------------------
    async def add_memory(
        self,
        user_id: str,
        fact_or_preference: str,
        metadata: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        memory_type: Optional[str] = None
    ) -> Optional[MemoryItem]:
        """Store a new long-term memory."""
        if not self.enabled:
            return None
        return await self.ltm.add_memory(
            user_id=user_id,
            content=fact_or_preference,
            conversation_id=conversation_id,
            memory_type=memory_type
        )

    async def remember(
        self,
        user_id: str,
        fact_or_preference: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Backward-compatible helper for legacy agents."""
        item = await self.add_memory(user_id=user_id, fact_or_preference=fact_or_preference, metadata=metadata)
        return item is not None

    def process_interaction_async(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        conversation_id: Optional[str] = None,
        source_message_id: Optional[str] = None
    ):
        """
        Non-blocking invocation of memory extraction.
        Schedules extraction as an async background task so streaming finishes immediately.
        Also records messages in STM fallback cache for immediate context availability.
        """
        if not self.enabled:
            return

        logger.info(
            f"[MEMORY] Processing interaction | user_id={user_id} | "
            f"conversation_id={conversation_id} | msg_len={len(user_message)}"
        )

        # Record in STM fallback cache immediately (non-blocking, synchronous)
        if conversation_id:
            try:
                self.stm.record_message_fallback(conversation_id, "user", user_message, source_message_id)
                self.stm.record_message_fallback(conversation_id, "assistant", assistant_response)
            except Exception as e:
                logger.debug(f"[STM] Fallback cache record note: {e}")

        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(
                self._safe_extract_from_dialog(
                    user_id=user_id,
                    user_message=user_message,
                    assistant_response=assistant_response,
                    conversation_id=conversation_id,
                    source_message_id=source_message_id
                )
            )
            if not hasattr(self, '_bg_tasks'):
                self._bg_tasks = set()
            self._bg_tasks.add(task)
            task.add_done_callback(self._bg_tasks.discard)
        except RuntimeError:
            # If called outside active event loop, run asynchronously
            try:
                asyncio.run(
                    self._safe_extract_from_dialog(
                        user_id=user_id,
                        user_message=user_message,
                        assistant_response=assistant_response,
                        conversation_id=conversation_id,
                        source_message_id=source_message_id
                    )
                )
            except Exception as e:
                logger.error(f"[MEMORY] Background extraction failed: {e}")

    async def _safe_extract_from_dialog(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        conversation_id: Optional[str] = None,
        source_message_id: Optional[str] = None
    ):
        """Safely wrap extract_from_dialog with structured logging and error handling."""
        try:
            logger.info(f"[MEMORY] Starting memory extraction for user '{user_id}'")
            await self.ltm.extract_from_dialog(
                user_id=user_id,
                user_message=user_message,
                assistant_response=assistant_response,
                conversation_id=conversation_id,
                source_message_id=source_message_id
            )
            logger.info(f"[MEMORY] Memory extraction completed for user '{user_id}'")
        except Exception as e:
            logger.error(f"[MEMORY] Memory extraction error for user '{user_id}': {e}", exc_info=True)

    # -------------------------------------------------------------------------
    # Search, Graph Context, and Deletion APIs
    # -------------------------------------------------------------------------
    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search relevant memories for a user or agent."""
        if not self.enabled:
            return []
        return await self.ltm.search(
            query=query,
            user_id=user_id,
            limit=limit,
            score_threshold=score_threshold
        )

    async def get_relevant_memories(self, user_id: str, query: str, limit: int = 3) -> List[str]:
        """Backward-compatible helper returning list of memory strings."""
        hits = await self.search(query=query, user_id=user_id, limit=limit)
        return [h.get("content", "") for h in hits if h.get("content")]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a persistent memory by ID."""
        return await self.ltm.delete_memory(memory_id)

    async def get_graph_context(self, query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Neo4j entity relationships for query."""
        return await self.graph.query_related_context(query, user_id=user_id)

    async def record_task_graph(
        self,
        task_id: str,
        task_type: str,
        tool_name: Optional[str] = None,
        document_name: Optional[str] = None
    ):
        """Record task execution provenance in Neo4j knowledge graph."""
        await self.graph.record_task_execution(
            task_id=task_id,
            task_type=task_type,
            tool_name=tool_name,
            document_name=document_name
        )

    # -------------------------------------------------------------------------
    # Unified Health Checks
    # -------------------------------------------------------------------------
    async def health_check(self) -> Dict[str, Any]:
        """
        Unified health check verifying MongoDB, Qdrant, Neo4j, Mem0, and Ollama embeddings.
        Returns exact status for every component.
        """
        stm_health = await self.stm.health_check()
        qdrant_health = await self.qdrant.health_check()
        neo4j_health = await self.graph.health_check()
        mem0_health = await self.mem0.health_check()
        emb_health = await self.embeddings.check_health()

        q_ok = qdrant_health.get("status") == "healthy"
        n_ok = neo4j_health.get("status") == "healthy"
        m_ok = mem0_health.get("status") == "healthy"
        e_ok = emb_health.get("status") == "healthy"
        s_ok = stm_health.get("status") in ["healthy", "degraded"]

        all_ok = q_ok and n_ok and m_ok and e_ok and s_ok
        overall_status = "healthy" if all_ok else "degraded"
        if not q_ok and not n_ok and not e_ok:
            overall_status = "unavailable"

        return {
            "memory": overall_status,
            "stm": stm_health.get("status", "unknown"),
            "ltm": "healthy" if (q_ok or m_ok) else "degraded",
            "qdrant": qdrant_health.get("status", "unknown"),
            "neo4j": neo4j_health.get("status", "unknown"),
            "mem0": mem0_health.get("status", "unknown"),
            "ollama": "healthy" if emb_health.get("available") else "unavailable",
            "embedding_model": emb_health.get("status", "unknown"),
            "details": {
                "qdrant": qdrant_health,
                "neo4j": neo4j_health,
                "mem0": mem0_health,
                "embedding": emb_health,
                "stm": stm_health
            }
        }


# Global singleton instance
memory_manager = MemoryManager()
