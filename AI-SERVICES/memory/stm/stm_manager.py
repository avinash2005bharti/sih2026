"""
Short-Term Memory (STM) Manager for Sovereign AI Workbench.
Retrieves active conversation history from MongoDB messages collection with local in-memory fallback.
Bounds message history and token usage to preserve prompt context.
"""

import os
import time
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo import MongoClient
from core.config import settings
from core.logging import logger
from memory.models import STMContext, STMMessage


class STMManager:
    """Manages active conversation window, message retrieval, and context caching."""

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        db_name: Optional[str] = None,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None,
        enabled: Optional[bool] = None
    ):
        self.enabled = (
            enabled
            if enabled is not None
            else (os.getenv("STM_ENABLED", "true").lower() == "true")
        )
        self.mongo_uri = (
            mongo_uri
            or os.getenv("MONGO_URI")
            or getattr(settings, "MONGO_URI", "mongodb://admin:admin@localhost:27017/sovereign_ai?authSource=admin")
        )
        self.db_name = (
            db_name
            or os.getenv("MONGO_DB_NAME")
            or getattr(settings, "MONGO_DB_NAME", "sovereign_ai")
        )
        self.max_messages = int(
            max_messages
            or os.getenv("STM_MAX_MESSAGES")
            or getattr(settings, "STM_MAX_MESSAGES", 20)
        )
        self.max_tokens = int(
            max_tokens
            or os.getenv("STM_MAX_TOKENS")
            or getattr(settings, "STM_MAX_TOKENS", 8000)
        )

        self._client: Optional[MongoClient] = None
        self._db: Optional[Any] = None
        # Local fallback cache: conversation_id -> list of STMMessage
        self._fallback_cache: Dict[str, List[STMMessage]] = {}
        logger.info(f"[STM] Initialized STMManager (Enabled: {self.enabled}, MaxMsgs: {self.max_messages}, MaxTokens: {self.max_tokens})")

    def _get_db(self) -> Optional[Any]:
        """Lazy connection to MongoDB with timeout."""
        if self._db is not None:
            return self._db

        uris = [self.mongo_uri]
        if "mongodb:27017" in self.mongo_uri:
            uris.append("mongodb://admin:admin@localhost:27017/sovereign_ai?authSource=admin")
            uris.append("mongodb://admin:admin@127.0.0.1:27017/sovereign_ai?authSource=admin")
        elif "localhost" in self.mongo_uri:
            uris.append(self.mongo_uri.replace("localhost", "127.0.0.1"))

        for u in uris:
            try:
                client = MongoClient(u, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
                client.admin.command("ping")
                self._client = client
                self._db = client[self.db_name]
                logger.info(f"[STM] Connected to MongoDB at {u}")
                return self._db
            except Exception as e:
                logger.debug(f"[STM] MongoDB connection failed for {u}: {e}")

        logger.warning("[STM] MongoDB currently unreachable. Operating with in-memory fallback.")
        return None

    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB connectivity and message collection health."""
        if not self.enabled:
            return {"status": "disabled", "detail": "STM is disabled via STM_ENABLED"}

        db = self._get_db()
        if db is not None:
            try:
                msg_count = db.messages.count_documents({})
                conv_count = db.conversations.count_documents({})
                return {
                    "status": "healthy",
                    "provider": "mongodb",
                    "total_messages": msg_count,
                    "total_conversations": conv_count
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "provider": "in_memory_fallback",
                    "error": str(e),
                    "cached_conversations": len(self._fallback_cache)
                }

        return {
            "status": "degraded",
            "provider": "in_memory_fallback",
            "cached_conversations": len(self._fallback_cache)
        }

    async def get_conversation_context(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> STMContext:
        """
        Retrieve recent conversation messages bounded by STM_MAX_MESSAGES.
        Queries MongoDB messages collection, falling back to local cache on error.
        """
        if not self.enabled or not conversation_id:
            return STMContext(conversation_id=conversation_id or "default", user_id=user_id, agent_id=agent_id)

        eff_limit = limit or self.max_messages
        messages: List[STMMessage] = []

        db = self._get_db()
        if db is not None:
            try:
                # Ensure performance indexes exist
                try:
                    db.messages.create_index([("conversation", 1), ("createdAt", -1)])
                    db.messages.create_index([("conversation_id", 1), ("createdAt", -1)])
                except Exception:
                    pass

                # Convert conversation_id to ObjectId if valid
                or_queries = [
                    {"conversation": str(conversation_id)},
                    {"conversation_id": str(conversation_id)}
                ]
                if ObjectId.is_valid(conversation_id):
                    or_queries.append({"conversation": ObjectId(conversation_id)})

                cursor = (
                    db.messages.find({"$or": or_queries})
                    .sort("createdAt", -1)
                    .limit(eff_limit)
                )
                raw_msgs = list(cursor)
                raw_msgs.reverse()  # Chronological order

                for m in raw_msgs:
                    sender = m.get("sender", m.get("role", "user"))
                    role = "user" if sender == "user" else "assistant"
                    messages.append(
                        STMMessage(
                            role=role,
                            content=m.get("content", ""),
                            message_id=str(m.get("_id", "")),
                            agent_id=str(m.get("agent", "")),
                            created_at=m.get("createdAt")
                        )
                    )
            except Exception as e:
                logger.warning(f"[STM] Failed querying MongoDB for {conversation_id}: {e}. Checking fallback cache.")
                messages = self._fallback_cache.get(conversation_id, [])[-eff_limit:]

            # If MongoDB has no messages for this conversation, check fallback cache
            if not messages and conversation_id in self._fallback_cache:
                messages = self._fallback_cache.get(conversation_id, [])[-eff_limit:]
        else:
            messages = self._fallback_cache.get(conversation_id, [])[-eff_limit:]

        # Estimate tokens roughly (~4 chars per token)
        total_chars = sum(len(m.content) for m in messages)
        est_tokens = total_chars // 4

        return STMContext(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_id=agent_id,
            messages=messages,
            estimated_tokens=est_tokens
        )

    async def record_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        model: Optional[str] = None,
        execution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Authoritative write to MongoDB messages collection and local fallback cache.
        Adheres strictly to Phase 3 requirements.
        """
        import datetime
        now = datetime.datetime.utcnow()
        msg_doc = {
            "conversation": ObjectId(conversation_id) if ObjectId.is_valid(conversation_id) else conversation_id,
            "conversation_id": str(conversation_id),
            "sender": "user" if role == "user" else "assistant",
            "role": role,
            "content": content,
            "createdAt": now,
            "updatedAt": now,
            "user_id": user_id,
            "agent": agent_id,
            "model": model,
            "execution_id": execution_id,
            "metadata": metadata or {},
            "attachments": attachments or []
        }

        db = self._get_db()
        if db is not None:
            try:
                res = db.messages.insert_one(msg_doc)
                msg_doc["_id"] = str(res.inserted_id)
            except Exception as e:
                logger.warning(f"[STM] Failed inserting message into MongoDB: {e}")

        # Also maintain in-memory cache
        self.record_message_fallback(conversation_id, role, content, message_id=str(msg_doc.get("_id", "")))
        return msg_doc

    def record_message_fallback(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None
    ):
        """Append message to in-memory fallback cache."""
        if not conversation_id:
            return
        if conversation_id not in self._fallback_cache:
            self._fallback_cache[conversation_id] = []

        self._fallback_cache[conversation_id].append(
            STMMessage(
                role=role,
                content=content,
                message_id=message_id,
                created_at=time.time()
            )
        )
        # Cap fallback cache length
        if len(self._fallback_cache[conversation_id]) > self.max_messages * 2:
            self._fallback_cache[conversation_id] = self._fallback_cache[conversation_id][-self.max_messages:]

    def clear_context(self, conversation_id: str):
        """Clear cached messages for a conversation."""
        if conversation_id in self._fallback_cache:
            del self._fallback_cache[conversation_id]


# Global singleton instance
stm_manager = STMManager()

