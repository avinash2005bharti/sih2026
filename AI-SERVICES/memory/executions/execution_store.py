"""
Execution Memory Store for Sovereign AI Workbench.
Persists and retrieves records of tool executions and actions across conversations.
Authoritative storage in MongoDB with in-memory fallback.
"""

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo import MongoClient

from core.config import settings
from core.logging import logger


class ExecutionStore:
    """Manages tracking and prompt-context injection for tool executions."""

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        db_name: Optional[str] = None
    ):
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
        self._client: Optional[MongoClient] = None
        self._db: Optional[Any] = None
        # Fallback cache: conversation_id -> list of execution records
        self._fallback_cache: Dict[str, List[Dict[str, Any]]] = {}

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
                try:
                    self._db.executions.create_index([("conversation", 1), ("createdAt", -1)])
                    self._db.executions.create_index([("conversation_id", 1), ("created_at", -1)])
                except Exception:
                    pass
                return self._db
            except Exception as e:
                logger.debug(f"[EXECUTION_STORE] MongoDB connect note for {u}: {e}")

        logger.warning("[EXECUTION_STORE] MongoDB currently unreachable. Operating with in-memory fallback.")
        return None

    def record_execution(
        self,
        conversation_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: Any,
        status: str = "completed",
        duration: float = 0.0,
        created_files: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None,
        execution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a completed or failed tool execution in MongoDB and local cache.
        """
        if not conversation_id:
            conversation_id = "default"

        exec_id = execution_id or f"exec_{int(time.time()*1000)}_{os.urandom(4).hex()}"
        now_dt = datetime.now(timezone.utc)

        doc: Dict[str, Any] = {
            "execution_id": exec_id,
            "conversation_id": conversation_id,
            "tool": tool_name,
            "action": tool_name,
            "arguments": tool_args,
            "input": tool_args,
            "output": result,
            "result": result,
            "status": status,
            "duration": duration,
            "created_files": created_files or [],
            "error": error,
            "user_id": user_id,
            "request_id": request_id,
            "task_id": task_id,
            "created_at": now_dt,
            "createdAt": now_dt,
            "updatedAt": now_dt,
        }

        if ObjectId.is_valid(conversation_id):
            doc["conversation"] = ObjectId(conversation_id)

        # 1. Store in MongoDB
        db = self._get_db()
        if db is not None:
            try:
                res = db.executions.insert_one(doc)
                doc["_id"] = str(res.inserted_id)
                logger.info(f"[EXECUTION_STORE] Recorded execution {tool_name} (id={exec_id}, status={status}) in MongoDB")
            except Exception as e:
                logger.error(f"[EXECUTION_STORE] Failed to persist execution in MongoDB: {e}")

        # 2. Update local fallback cache
        if conversation_id not in self._fallback_cache:
            self._fallback_cache[conversation_id] = []
        self._fallback_cache[conversation_id].append(doc)

        return doc

    def get_recent_executions(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent tool executions for a conversation.
        """
        if not conversation_id:
            return []

        executions: List[Dict[str, Any]] = []
        db = self._get_db()

        if db is not None:
            try:
                queries = [{"conversation_id": conversation_id}]
                if ObjectId.is_valid(conversation_id):
                    queries.append({"conversation": ObjectId(conversation_id)})

                cursor = (
                    db.executions.find({"$or": queries})
                    .sort("createdAt", -1)
                    .limit(limit)
                )
                for item in cursor:
                    item["_id"] = str(item.get("_id", ""))
                    executions.append(item)
            except Exception as e:
                logger.warning(f"[EXECUTION_STORE] MongoDB query error for conv={conversation_id}: {e}")

        if not executions and conversation_id in self._fallback_cache:
            executions = list(self._fallback_cache[conversation_id])[-limit:]

        return executions

    def format_executions_for_prompt(self, executions: List[Dict[str, Any]]) -> str:
        """
        Format recent executions into clean Markdown for prompt context.
        """
        if not executions:
            return ""

        lines = ["### Recent Tool Executions in this Conversation:"]
        for idx, ex in enumerate(executions, 1):
            tool = ex.get("tool", "unknown_tool")
            status = ex.get("status", "completed")
            dur = ex.get("duration", 0.0)
            args_str = str(ex.get("arguments", {}))
            if len(args_str) > 120:
                args_str = args_str[:120] + "..."
            cfiles = ex.get("created_files", [])
            cfile_str = f" | Created Files: {[f.get('name') or f.get('filename') for f in cfiles]}" if cfiles else ""
            lines.append(f"{idx}. Tool: `{tool}` | Status: {status} ({dur}s) | Args: {args_str}{cfile_str}")

        lines.append("\nNote: When the user asks what tools you executed or whether an execution succeeded, refer directly to this verified execution record.")
        return "\n".join(lines)


# Global singleton instance
execution_store = ExecutionStore()
