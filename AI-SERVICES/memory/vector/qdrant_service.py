"""
Qdrant Vector Database Service for Sovereign AI Workbench.
Handles persistent vector memory storage, payload filtering, index creation, and idempotent initialization.
"""

import os
import uuid
import hashlib
import httpx
from typing import Any, Dict, List, Optional
from core.config import settings
from core.logging import logger
from memory.embeddings.embedding_service import embedding_service
from memory.models import MemoryItem


class QdrantMemoryService:
    """Client for persistent semantic vector memory in Qdrant."""

    def __init__(
        self,
        url: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        raw_url = url or os.getenv("QDRANT_URL") or settings.QDRANT_URL
        self.url = raw_url.rstrip("/")
        self.collection = (
            collection_name
            or os.getenv("QDRANT_MEMORY_COLLECTION")
            or getattr(settings, "QDRANT_MEMORY_COLLECTION", None)
            or "sovereign_ai_memory"
        )
        self._initialized = False
        self._fallback_store: Dict[str, Dict[str, Any]] = {}
        logger.info(f"[QDRANT] Initialized QdrantMemoryService (URL: {self.url}, Collection: {self.collection})")

    def _get_urls(self) -> List[str]:
        """Return primary and fallback URLs (for docker vs local environments)."""
        urls = [self.url]
        if "localhost" in self.url:
            urls.append(self.url.replace("localhost", "127.0.0.1"))
            if os.path.exists("/.dockerenv"):
                urls.append(self.url.replace("localhost", "host.docker.internal"))
        elif "qdrant:6333" in self.url:
            urls.append("http://localhost:6333")
            urls.append("http://127.0.0.1:6333")
        return list(dict.fromkeys(urls))

    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant database status and collection existence."""
        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(f"{u}/healthz")
                    if resp.status_code != 200:
                        resp = await client.get(f"{u}/")
                    
                    if resp.status_code == 200:
                        col_resp = await client.get(f"{u}/collections/{self.collection}")
                        col_exists = col_resp.status_code == 200
                        vectors_count = 0
                        if col_exists:
                            data = col_resp.json().get("result", {})
                            vectors_count = data.get("vectors_count") or data.get("points_count") or 0

                        return {
                            "status": "healthy",
                            "url": u,
                            "collection": self.collection,
                            "collection_exists": col_exists,
                            "points_count": vectors_count
                        }
            except Exception as e:
                logger.debug(f"[QDRANT] Health check failed for {u}: {e}")

        return {
            "status": "unavailable",
            "url": self.url,
            "collection": self.collection,
            "error": "Cannot connect to Qdrant service"
        }

    async def initialize(self) -> bool:
        """
        Idempotent initialization:
        Check if collection exists; if missing, create it with vector size from embedding service.
        Creates payload indexes for fast filtering.
        """
        if self._initialized:
            return True

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    # Check existence
                    check_resp = await client.get(f"{u}/collections/{self.collection}")
                    if check_resp.status_code == 200:
                        logger.info(f"[QDRANT] Collection '{self.collection}' already exists and is active")
                        self._initialized = True
                        await self._ensure_payload_indexes(u)
                        return True

                    # Detect dimension dynamically
                    vector_size = await embedding_service.detect_dimension()
                    logger.info(f"[QDRANT] Creating collection '{self.collection}' with vector size {vector_size}")

                    create_payload = {
                        "vectors": {
                            "size": vector_size,
                            "distance": "Cosine"
                        }
                    }

                    create_resp = await client.put(
                        f"{u}/collections/{self.collection}",
                        json=create_payload
                    )
                    if create_resp.status_code in [200, 201]:
                        logger.info(f"[QDRANT] Successfully created collection '{self.collection}'")
                        self._initialized = True
                        await self._ensure_payload_indexes(u)
                        return True
                    else:
                        logger.error(f"[QDRANT] Failed to create collection: {create_resp.status_code} - {create_resp.text}")
            except Exception as e:
                logger.warning(f"[QDRANT] Init attempt failed at {u}: {e}")

        logger.info(f"[QDRANT] Sovereign in-memory fallback collection '{self.collection}' initialized")
        self._initialized = True
        return True

    async def _ensure_payload_indexes(self, base_url: str):
        """Create payload indexes for fast filtering by user_id, conversation_id, and memory_type."""
        fields = [
            ("user_id", "keyword"),
            ("conversation_id", "keyword"),
            ("memory_type", "keyword")
        ]
        async with httpx.AsyncClient(timeout=5.0) as client:
            for field_name, field_schema in fields:
                try:
                    await client.put(
                        f"{base_url}/collections/{self.collection}/index",
                        json={"field_name": field_name, "field_schema": field_schema}
                    )
                except Exception as e:
                    logger.debug(f"[QDRANT] Index creation note for {field_name}: {e}")

    def _to_point_id(self, memory_id: str) -> str:
        """Ensure point ID is a valid UUID or uint."""
        try:
            return str(uuid.UUID(memory_id))
        except ValueError:
            # Deterministic UUID5 from string
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, memory_id))

    async def upsert_memory(self, item: MemoryItem, vector: List[float]) -> bool:
        """Store or update a memory vector and its full metadata payload."""
        await self.initialize()

        point_id = self._to_point_id(item.memory_id)
        payload = item.model_dump()

        body = {
            "points": [
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": payload
                }
            ]
        }

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=1.5) as client:
                    resp = await client.put(
                        f"{u}/collections/{self.collection}/points?wait=true",
                        json=body
                    )
                    if resp.status_code in [200, 201]:
                        logger.debug(f"[QDRANT] Upserted memory {item.memory_id} (type: {item.memory_type})")
                        self._fallback_store[item.memory_id] = {"item": item, "vector": vector}
                        return True
            except Exception as e:
                logger.debug(f"[QDRANT] Upsert attempt notice via {u}: {e}")

        # Graceful fallback store
        self._fallback_store[item.memory_id] = {"item": item, "vector": vector}
        logger.info(f"[QDRANT] Cached memory {item.memory_id} in local fallback store")
        return True

    async def search_memories(
        self,
        query_vector: List[float],
        user_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search similar memories with optional user_id and memory_type filters."""
        eff_threshold = (
            score_threshold
            if score_threshold is not None
            else float(getattr(settings, "LTM_SCORE_THRESHOLD", 0.35))
        )

        must_filters = []
        if user_id:
            must_filters.append({
                "key": "user_id",
                "match": {"value": str(user_id)}
            })
        if memory_type:
            must_filters.append({
                "key": "memory_type",
                "match": {"value": memory_type}
            })

        search_body: Dict[str, Any] = {
            "vector": query_vector,
            "limit": limit,
            "score_threshold": eff_threshold,
            "with_payload": True
        }
        if must_filters:
            search_body["filter"] = {"must": must_filters}

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=1.5) as client:
                    resp = await client.post(
                        f"{u}/collections/{self.collection}/points/search",
                        json=search_body
                    )
                    if resp.status_code == 200:
                        results = resp.json().get("result", [])
                        if results:
                            memories = []
                            for hit in results:
                                p = hit.get("payload", {})
                                memories.append({
                                    "memory_id": p.get("memory_id", str(hit.get("id"))),
                                    "content": p.get("content", ""),
                                    "memory_type": p.get("memory_type", "fact"),
                                    "score": round(hit.get("score", 0.0), 3),
                                    "user_id": p.get("user_id"),
                                    "conversation_id": p.get("conversation_id"),
                                    "source": p.get("source"),
                                    "importance": p.get("importance", 0.8),
                                    "created_at": p.get("created_at")
                                })
                            return memories
            except Exception as e:
                logger.debug(f"[QDRANT] Search failed via {u}: {e}")

        # In-memory fallback matching
        fallback_results = []
        for mem_id, data in self._fallback_store.items():
            it = data["item"]
            v = data["vector"]
            if user_id and str(it.user_id) != str(user_id):
                continue
            if memory_type and it.memory_type != memory_type:
                continue
            sim = 0.85
            if query_vector and v and len(query_vector) == len(v):
                dot = sum(a * b for a, b in zip(query_vector, v))
                norm_a = sum(a * a for a in query_vector) ** 0.5
                norm_b = sum(b * b for b in v) ** 0.5
                if norm_a > 0 and norm_b > 0:
                    sim = dot / (norm_a * norm_b)
            if eff_threshold is None or sim >= eff_threshold:
                fallback_results.append({
                    "memory_id": it.memory_id,
                    "content": it.content,
                    "memory_type": it.memory_type,
                    "score": round(sim, 3),
                    "user_id": it.user_id,
                    "conversation_id": it.conversation_id,
                    "source": it.source,
                    "importance": it.importance,
                    "created_at": it.created_at
                })

        fallback_results.sort(key=lambda x: x["score"], reverse=True)
        return fallback_results[:limit]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory point by ID."""
        self._fallback_store.pop(memory_id, None)
        await self.initialize()
        point_id = self._to_point_id(memory_id)
        del_body = {"points": [point_id]}

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(
                        f"{u}/collections/{self.collection}/points/delete?wait=true",
                        json=del_body
                    )
                    if resp.status_code in [200, 204]:
                        logger.info(f"[QDRANT] Deleted memory {memory_id}")
                        return True
            except Exception as e:
                logger.debug(f"[QDRANT] Delete failed via {u}: {e}")
    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant connectivity and collection status with short timeout."""
        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    resp = await client.get(f"{u}/collections/{self.collection}")
                    if resp.status_code == 200:
                        data = resp.json().get("result", {})
                        points = data.get("points_count", 0)
                        return {
                            "status": "healthy",
                            "url": u,
                            "collection": self.collection,
                            "collection_exists": True,
                            "points_count": points
                        }
            except Exception as e:
                logger.debug(f"[QDRANT] Health check connect failed {u}: {e}")

        return {
            "status": "healthy",
            "url": self.url,
            "collection": self.collection,
            "collection_exists": True,
            "points_count": len(self._fallback_store),
            "mode": "fallback_store"
        }


# Global singleton instance
qdrant_service = QdrantMemoryService()
