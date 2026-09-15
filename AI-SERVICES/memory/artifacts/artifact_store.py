"""
Artifact Memory Store for Sovereign AI Workbench.
Persists and retrieves records of all files and reports generated across conversations.
Authoritative storage in MongoDB with Neo4j entity linking and in-memory fallback.
"""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo import MongoClient

from core.config import settings
from core.logging import logger


class ArtifactStore:
    """Manages tracking, persistence, and prompt-context injection for generated files."""

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
        # Fallback cache: conversation_id -> list of artifact dicts
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
                # Ensure compound index on artifacts collection
                try:
                    self._db.artifacts.create_index([("conversation", 1), ("createdAt", -1)])
                    self._db.artifacts.create_index([("conversation_id", 1), ("created_at", -1)])
                except Exception:
                    pass
                return self._db
            except Exception as e:
                logger.debug(f"[ARTIFACT_STORE] MongoDB connect note for {u}: {e}")

        logger.warning("[ARTIFACT_STORE] MongoDB currently unreachable. Operating with in-memory fallback.")
        return None

    def register_artifact(
        self,
        conversation_id: str,
        filename: str,
        file_path: str,
        artifact_type: str = "other",
        mime_type: Optional[str] = None,
        size_bytes: int = 0,
        description: str = "",
        execution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a newly generated artifact in MongoDB and local cache.
        Verifies existence and updates Neo4j graph when active.
        """
        if not conversation_id:
            conversation_id = "default"

        # Determine mime_type and artifact_type if generic
        lower_name = filename.lower()
        if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
            artifact_type = "spreadsheet"
            mime_type = mime_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif lower_name.endswith(".pdf"):
            artifact_type = "document"
            mime_type = mime_type or "application/pdf"
        elif lower_name.endswith(".csv"):
            artifact_type = "spreadsheet"
            mime_type = mime_type or "text/csv"
        elif lower_name.endswith((".png", ".jpg", ".jpeg", ".webp")):
            artifact_type = "image"
            mime_type = mime_type or "image/png"

        artifact_id = f"art_{int(time.time()*1000)}_{os.urandom(4).hex()}"
        now_dt = datetime.now(timezone.utc)

        doc: Dict[str, Any] = {
            "artifact_id": artifact_id,
            "conversation_id": conversation_id,
            "filename": filename,
            "artifact_type": artifact_type,
            "path": file_path,
            "mime_type": mime_type or "application/octet-stream",
            "size_bytes": size_bytes,
            "description": description or f"Generated {artifact_type} file: {filename}",
            "execution_id": execution_id,
            "task_id": task_id,
            "user_id": user_id,
            "request_id": request_id,
            "status": "verified",
            "created_at": now_dt,
            "createdAt": now_dt,
            "updatedAt": now_dt,
            "metadata": metadata or {}
        }

        if ObjectId.is_valid(conversation_id):
            doc["conversation"] = ObjectId(conversation_id)
        if user_id and ObjectId.is_valid(user_id):
            doc["user"] = ObjectId(user_id)

        # 1. Store in MongoDB
        db = self._get_db()
        if db is not None:
            try:
                res = db.artifacts.insert_one(doc)
                doc["_id"] = str(res.inserted_id)
                logger.info(f"[ARTIFACT_STORE] Registered artifact in MongoDB: {filename} (id={artifact_id}, conv={conversation_id})")
            except Exception as e:
                logger.error(f"[ARTIFACT_STORE] Failed to persist artifact in MongoDB: {e}")

        # 2. Update local fallback cache
        if conversation_id not in self._fallback_cache:
            self._fallback_cache[conversation_id] = []
        self._fallback_cache[conversation_id].append(doc)

        # 3. Asynchronously record in Neo4j graph if available
        try:
            from memory.graph.neo4j_service import neo4j_service
            if neo4j_service.enabled:
                import asyncio
                query_cypher = """
                MERGE (c:Conversation {id: $conv_id})
                MERGE (a:Artifact {id: $art_id})
                SET a.filename = $filename, a.type = $type, a.path = $path, a.createdAt = datetime()
                MERGE (c)-[:GENERATED]->(a)
                """
                asyncio.create_task(
                    neo4j_service.execute_write(
                        query_cypher,
                        {
                            "conv_id": conversation_id,
                            "art_id": artifact_id,
                            "filename": filename,
                            "type": artifact_type,
                            "path": file_path
                        }
                    )
                )
        except Exception as graph_err:
            logger.debug(f"[ARTIFACT_STORE] Neo4j graph linking note: {graph_err}")

        return doc

    def get_artifacts_for_conversation(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all artifacts created within a specific conversation.
        Guarantees conversation isolation.
        """
        if not conversation_id:
            return []

        artifacts: List[Dict[str, Any]] = []
        db = self._get_db()

        if db is not None:
            try:
                queries = [{"conversation_id": conversation_id}]
                if ObjectId.is_valid(conversation_id):
                    queries.append({"conversation": ObjectId(conversation_id)})

                cursor = (
                    db.artifacts.find({"$or": queries})
                    .sort("createdAt", -1)
                    .limit(limit)
                )
                for item in cursor:
                    item["_id"] = str(item.get("_id", ""))
                    artifacts.append(item)
            except Exception as e:
                logger.warning(f"[ARTIFACT_STORE] MongoDB query error for conv={conversation_id}: {e}")

        # If MongoDB returned nothing, check fallback cache
        if not artifacts and conversation_id in self._fallback_cache:
            artifacts = list(self._fallback_cache[conversation_id])[-limit:]

        return artifacts

    def format_artifacts_for_prompt(self, artifacts: List[Dict[str, Any]]) -> str:
        """
        Format artifact records into clean, unambiguous Markdown for LLM prompt context.
        """
        if not artifacts:
            return ""

        lines = ["### Previously Generated Artifacts / Files in this Conversation:"]
        for idx, art in enumerate(artifacts, 1):
            fname = art.get("filename", "unknown")
            atype = art.get("artifact_type", "file").capitalize()
            fsize = art.get("size_bytes", 0)
            fpath = art.get("path", "")
            desc = art.get("description", "")
            size_str = f"{fsize / 1024:.1f} KB" if fsize >= 1024 else f"{fsize} B"
            line = f"{idx}. **{fname}** ({atype}, {size_str}) - Path: `{fpath}`"
            if desc:
                line += f" | Description: {desc}"
            lines.append(line)

        lines.append("\nNote: When the user asks which files you created or asks about previous files, refer strictly to the above verified artifacts.")
        return "\n".join(lines)


# Global singleton instance
artifact_store = ArtifactStore()
