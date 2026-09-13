"""
Unified Memory Manager for Sovereign AI Workbench.
Coordinates:
1. Mem0: Long-term user memories, preferences, and facts.
2. Qdrant: Raw vector similarity search over documents.
3. Neo4j: Structured knowledge graph relationships.
"""

from typing import Any, Dict, List, Optional
from memory.mem0_client import mem0_client
from memory.neo4j_client import neo4j_client
from rag.retriever import rag_retriever
from core.logging import logger


class MemoryManager:
    """Coordinates memory retrieval and graph querying to enrich agent prompts."""

    def __init__(self):
        self.mem0 = mem0_client
        self.graph = neo4j_client
        self.retriever = rag_retriever

    async def remember(self, user_id: str, fact_or_preference: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store long-term memory fact via Mem0."""
        return await self.mem0.add_memory(user_id, fact_or_preference, metadata)

    async def get_relevant_memories(self, user_id: str, query: str, limit: int = 3) -> List[str]:
        """Fetch relevant user memories."""
        items = await self.mem0.search_memories(user_id, query, limit=limit)
        return [item["text"] for item in items if item.get("text")]

    async def record_task_graph(
        self,
        task_id: str,
        task_type: str,
        tool_name: Optional[str] = None,
        document_name: Optional[str] = None
    ):
        """Record node in Neo4j knowledge graph."""
        await self.graph.record_task_execution(
            task_id=task_id,
            task_type=task_type,
            tool_name=tool_name,
            document_name=document_name
        )

    async def build_enriched_context(self, user_id: str, query: str) -> str:
        """
        Build enriched context string to prepend to agent system prompt before generation.
        Includes recalled memories and relevant knowledge base excerpts.
        """
        context_parts = []

        # 1. Fetch relevant user memories
        memories = await self.get_relevant_memories(user_id, query, limit=3)
        if memories:
            context_parts.append("### Recalled Long-Term User Facts & Preferences:")
            for m in memories:
                context_parts.append(f"- {m}")

        return "\n".join(context_parts) if context_parts else ""


# Global singleton instance
memory_manager = MemoryManager()
