"""
Local Mem0 Memory Client for Sovereign AI Workbench.
Uses Qdrant collection 'sovereign_memories' as the vector backend
and Ollama's nomic-embed-text for local embeddings.
"""

import time
import hashlib
from typing import Any, Dict, List, Optional
from rag.embeddings import embeddings_service
from rag.qdrant_client import QdrantClient
from core.logging import logger

MEMORIES_COLLECTION = "sovereign_memories"


class Mem0MemoryClient:
    """Manages long-term episodic memory (facts, preferences, outcomes) for users."""

    def __init__(self):
        self.qdrant = QdrantClient(collection=MEMORIES_COLLECTION)
        self._initialized = False

    async def initialize(self) -> bool:
        """Ensure memories collection exists in Qdrant."""
        if self._initialized:
            return True
        try:
            created = await self.qdrant.create_collection()
            self._initialized = True
            logger.info(f"[MEM0] Initialized memory collection: '{MEMORIES_COLLECTION}'")
            return created
        except Exception as e:
            logger.warning(f"[MEM0] Memory collection init error: {e}")
            return False

    async def add_memory(self, user_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store a long-term memory fact or user preference."""
        await self.initialize()
        try:
            vector = await embeddings_service.get_embedding(text)
            if not vector:
                return False

            point_id = int(hashlib.md5(f"{user_id}_{text}".encode("utf-8")).hexdigest()[:8], 16)
            payload = {
                "user_id": user_id,
                "text": text,
                "created_at": time.time(),
                **(metadata or {})
            }

            return await self.qdrant.upsert_points([{
                "id": point_id,
                "vector": vector,
                "payload": payload
            }])
        except Exception as e:
            logger.error(f"[MEM0] Failed to store memory: {e}")
            return False

    async def search_memories(self, user_id: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant long-term memories for a given user and query."""
        await self.initialize()
        try:
            vector = await embeddings_service.get_embedding(query)
            if not vector:
                return []

            points = await self.qdrant.search(
                query_vector=vector,
                limit=limit,
                score_threshold=0.60
            )

            # Filter by user_id
            results = []
            for p in points:
                payload = p.get("payload", {})
                if payload.get("user_id") == user_id or payload.get("user_id") == "system":
                    results.append({
                        "text": payload.get("text", ""),
                        "score": round(p.get("score", 0.0), 3),
                        "created_at": payload.get("created_at")
                    })
            return results
        except Exception as e:
            logger.error(f"[MEM0] Memory search error: {e}")
            return []


# Global singleton instance
mem0_client = Mem0MemoryClient()
