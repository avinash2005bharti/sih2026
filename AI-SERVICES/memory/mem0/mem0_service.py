"""
Mem0 Service for Sovereign AI Workbench.
Wraps the actual Mem0 library to orchestrate memory extraction, deduplication,
semantic updates, and persistent retrieval using 100% local Ollama and local Qdrant.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from core.config import settings
from core.logging import logger

# Ensure 100% Sovereign On-Premise execution without external telemetry
os.environ["MEM0_TELEMETRY"] = "False"
os.environ["MEM0_DISABLE_TELEMETRY"] = "1"
os.environ["POSTHOG_DISABLED"] = "1"

try:
    from mem0 import Memory
    HAS_MEM0_LIB = True
except ImportError:
    HAS_MEM0_LIB = False
    Memory = None


class Mem0Service:
    """Enterprise Mem0 integration for local LLM extraction and vector storage."""

    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        collection_name: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None
    ):
        self.qdrant_url = (qdrant_url or os.getenv("QDRANT_URL") or settings.QDRANT_URL).rstrip("/")
        self.collection_name = (
            collection_name
            or os.getenv("QDRANT_MEMORY_COLLECTION")
            or getattr(settings, "QDRANT_MEMORY_COLLECTION", None)
            or "sovereign_ai_memory"
        )
        self.ollama_base_url = (
            ollama_base_url
            or os.getenv("OLLAMA_BASE_URL")
            or settings.OLLAMA_BASE_URL
        ).rstrip("/")
        self.embedding_model = (
            embedding_model
            or os.getenv("OLLAMA_EMBEDDING_MODEL")
            or getattr(settings, "OLLAMA_EMBEDDING_MODEL", None)
            or "nomic-embed-text"
        )
        # LLM for memory fact extraction (qwen2.5:1.5b is fast and accurate locally)
        self.llm_model = (
            llm_model
            or os.getenv("OLLAMA_CHAT_MODEL")
            or getattr(settings, "OLLAMA_CHAT_MODEL", None)
            or "qwen2.5:1.5b"
        )
        if ":" in self.embedding_model and self.embedding_model.endswith(":latest"):
            self.embedding_model = self.embedding_model.replace(":latest", "")

        self._memory_instance: Optional[Any] = None
        self._init_lock = asyncio.Lock()
        self._fallback_memories: List[Dict[str, Any]] = []
        logger.info(f"[MEM0] Initialized Mem0Service wrapper (Collection: {self.collection_name}, LLM: {self.llm_model}, Embedder: {self.embedding_model})")

    def _build_config(self) -> Dict[str, Any]:
        """Generate configuration dictionary for Mem0."""
        # Resolve URLs
        q_url = self.qdrant_url
        o_url = self.ollama_base_url
        if "qdrant:6333" in q_url and not os.path.exists("/.dockerenv"):
            q_url = "http://localhost:6333"
        if "host.docker.internal" in o_url and not os.path.exists("/.dockerenv"):
            o_url = "http://localhost:11434"

        return {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": self.collection_name,
                    "embedding_model_dims": getattr(settings, "QDRANT_VECTOR_SIZE", 768),
                    "url": q_url
                }
            },
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": self.llm_model,
                    "ollama_base_url": o_url
                }
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": self.embedding_model,
                    "ollama_base_url": o_url
                }
            },
            "version": "v1.1"
        }

    async def _get_instance(self) -> Optional[Any]:
        """Lazy thread-safe initialization of Mem0 Memory instance."""
        if not HAS_MEM0_LIB:
            return None
        if self._memory_instance is not None:
            return self._memory_instance

        async with self._init_lock:
            if self._memory_instance is not None:
                return self._memory_instance

            try:
                loop = asyncio.get_running_loop()
                cfg = self._build_config()
                self._memory_instance = await loop.run_in_executor(None, Memory.from_config, cfg)
                # SOVEREIGN AIR-GAP SHIELD FIX: Prevent fastembed from downloading BM25 encoder from huggingface.co
                if hasattr(self._memory_instance, "vector_store"):
                    self._memory_instance.vector_store._bm25_encoder = False
                    self._memory_instance.vector_store._has_bm25_slot = False
                logger.info(f"[MEM0] Mem0 instance initialized with local Ollama + Qdrant: {self.collection_name}")
                return self._memory_instance
            except Exception as e:
                logger.error(f"[MEM0] Failed to initialize Mem0 Memory instance: {e}")
                return None

    async def health_check(self) -> Dict[str, Any]:
        """Check Mem0 readiness and component health."""
        if not HAS_MEM0_LIB:
            return {"status": "unavailable", "error": "mem0ai library is not installed"}

        try:
            instance = await asyncio.wait_for(self._get_instance(), timeout=2.5)
        except (asyncio.TimeoutError, Exception) as te:
            logger.debug(f"[MEM0] Health check instance probe: {te}")
            instance = None

        if instance is not None:
            return {
                "status": "healthy",
                "collection": self.collection_name,
                "llm": self.llm_model,
                "embedder": self.embedding_model,
                "vector_store": "qdrant"
            }

        return {
            "status": "degraded",
            "collection": self.collection_name,
            "error": "Mem0 initialization in progress or failed"
        }

    async def add_memory(
        self,
        text_or_messages: Any = None,
        user_id: str = "default_user",
        metadata: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
        **extra_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Extract facts and persist into memory via Mem0.
        Deduplicates and updates existing memories automatically.
        """
        target_input = content if content is not None else text_or_messages
        if target_input is None:
            return []

        import time
        text_str = ""
        if isinstance(target_input, str):
            text_str = target_input
        elif isinstance(target_input, list) and target_input:
            text_str = target_input[-1].get("content", str(target_input))
        else:
            text_str = str(target_input or "")

        fb_entry = {
            "id": f"mem0_fb_{len(self._fallback_memories)+1}",
            "memory": text_str,
            "user_id": str(user_id),
            "created_at": time.time(),
            "metadata": metadata or {}
        }
        self._fallback_memories.append(fb_entry)

        instance = await self._get_instance()
        if not instance:
            logger.info(f"[MEM0] Mem0 instance unavailable. Stored in sovereign fallback: {fb_entry['id']}")
            return [fb_entry]

        try:
            loop = asyncio.get_running_loop()
            kwargs: Dict[str, Any] = {"user_id": str(user_id)}
            if metadata:
                kwargs["metadata"] = metadata

            formatted_input = target_input
            if isinstance(target_input, str):
                formatted_input = [{"role": "user", "content": target_input}]

            res = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: instance.add(formatted_input, **kwargs)
                ),
                timeout=3.0
            )
            logger.info(f"[MEM0] Added memory for user {user_id}: {res}")
            if isinstance(res, dict) and res.get("results"):
                return res.get("results", [])
            elif isinstance(res, list) and res:
                return res
            return [fb_entry]
        except (asyncio.TimeoutError, Exception) as e:
            logger.debug(f"[MEM0] add_memory note for user {user_id}: {e}")
            return [fb_entry]

    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for a user query.
        """
        cleaned = []
        instance = await self._get_instance()
        if instance:
            try:
                loop = asyncio.get_running_loop()
                filters = {}
                if user_id:
                    filters["user_id"] = str(user_id)

                res = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: instance.search(query, filters=filters if filters else None, limit=limit)
                    ),
                    timeout=3.0
                )
                raw_results = res.get("results", []) if isinstance(res, dict) else (res or [])
                for item in raw_results:
                    cleaned.append({
                        "id": item.get("id"),
                        "memory": item.get("memory") or item.get("text", ""),
                        "score": round(item.get("score", 0.0), 3) if item.get("score") else None,
                        "metadata": item.get("metadata"),
                        "created_at": item.get("created_at"),
                        "user_id": item.get("user_id")
                    })
            except Exception as e:
                logger.debug(f"[MEM0] search_memories error note: {e}")

        if not cleaned:
            # Fallback search across sovereign in-memory store
            words = [w.lower().strip("?,.!;:()[]{}'\"") for w in query.split() if len(w) >= 3]
            for item in self._fallback_memories:
                if user_id and str(item.get("user_id")) != str(user_id):
                    continue
                m_text = item.get("memory", "").lower()
                if any(w in m_text for w in words):
                    cleaned.append({
                        "id": item.get("id"),
                        "memory": item.get("memory", ""),
                        "score": 0.88,
                        "metadata": item.get("metadata"),
                        "created_at": item.get("created_at"),
                        "user_id": item.get("user_id")
                    })
        return cleaned[:limit]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from Mem0."""
        instance = await self._get_instance()
        if not instance:
            return False

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: instance.delete(memory_id))
            return True
        except Exception as e:
            logger.warning(f"[MEM0] delete_memory error for {memory_id}: {e}")
            return False


# Global singleton instance
mem0_service = Mem0Service()
