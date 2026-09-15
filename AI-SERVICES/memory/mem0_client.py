"""
Compatibility bridge for Mem0MemoryClient.
Delegates to the official Mem0Service and QdrantMemoryService.
"""

from typing import Any, Dict, List, Optional
from memory.mem0.mem0_service import mem0_service
from memory.vector.qdrant_service import qdrant_service
from memory.ltm.ltm_manager import ltm_manager
from core.logging import logger


class Mem0MemoryClient:
    """Compatibility wrapper delegating to official Mem0Service and LTMManager."""

    def __init__(self):
        self.mem0 = mem0_service
        self.qdrant = qdrant_service

    async def initialize(self) -> bool:
        """Initialize Qdrant collection."""
        return await self.qdrant.initialize()

    async def add_memory(self, user_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store long-term memory via LTMManager."""
        item = await ltm_manager.add_memory(
            user_id=user_id,
            content=text,
            conversation_id=metadata.get("conversation_id") if metadata else None
        )
        return item is not None

    async def search_memories(self, user_id: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search memories via LTMManager."""
        hits = await ltm_manager.search(query=query, user_id=user_id, limit=limit)
        results = []
        for h in hits:
            results.append({
                "text": h.get("content", ""),
                "score": h.get("score", 0.0),
                "created_at": h.get("created_at")
            })
        return results


# Global singleton instance
mem0_client = Mem0MemoryClient()
