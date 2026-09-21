"""
Central Document Store for Sovereign AI Workbench.
Coordinates document records in MongoDB and vector indices in Qdrant,
providing complete CRUD operations for both system endpoints and autonomous agents.
"""

import os
import re
import time
import uuid
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo import MongoClient

from core.config import settings
from core.logging import logger
from rag.retriever import rag_retriever
from rag.chunker import text_chunker

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = (BASE_DIR / "workspace").resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTS_DIR = (WORKSPACE_DIR / "reports").resolve()
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

# Search roots for user uploaded documents across backend and data uploads
CANDIDATE_SEARCH_DIRS = [
    (BASE_DIR.parent / "BACKEND" / "uploads" / "documents").resolve(),
    (BASE_DIR / "data" / "uploads").resolve(),
]


class DocumentStore:
    """Manages document CRUD across MongoDB and Qdrant with universal disk fallback."""

    def __init__(self):
        self.mongo_uri = settings.MONGO_URI
        self.db_name = settings.MONGO_DB_NAME
        self._client: Optional[MongoClient] = None
        self._db: Optional[Any] = None
        self._last_mongo_check: float = 0

    def _get_db(self) -> Optional[Any]:
        """Lazy connection to MongoDB with cached retry backoff."""
        if self._db is not None:
            return self._db

        now = time.time()
        if now - self._last_mongo_check < 15.0:
            return None
        self._last_mongo_check = now

        uris = [
            self.mongo_uri,
            "mongodb://127.0.0.1:27017/sovereign_ai",
            "mongodb://localhost:27017/sovereign_ai",
            "mongodb://admin:admin@127.0.0.1:27017/sovereign_ai?authSource=admin",
            "mongodb://admin:admin@localhost:27017/sovereign_ai?authSource=admin",
        ]

        for u in uris:
            try:
                client = MongoClient(u, serverSelectionTimeoutMS=800, connectTimeoutMS=800)
                client.admin.command("ping")
                self._client = client
                self._db = client[self.db_name]
                logger.info(f"[DocumentStore] Connected to MongoDB at {u}")
                return self._db
            except Exception as e:
                logger.debug(f"[DocumentStore] MongoDB connection attempt failed for {u}: {e}")

        logger.warning("[DocumentStore] MongoDB unreachable, operating in local disk/workspace mode.")
        return None

    def _serialize_doc(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document ObjectId and dates to JSON-serializable format with standardized aliases."""
        if not doc:
            return {}
        result = dict(doc)
        if "_id" in result:
            result["_id"] = str(result["_id"])
            result["document_id"] = str(result["_id"])
        if "uploadedBy" in result and isinstance(result["uploadedBy"], ObjectId):
            result["uploadedBy"] = str(result["uploadedBy"])
        for k, v in result.items():
            if isinstance(v, (datetime.datetime, datetime.date)):
                result[k] = v.isoformat()
        
        # Standardize aliases so both Python and Node.js conventions work
        if "name" in result and "title" not in result:
            result["title"] = result["name"]
        elif "title" in result and "name" not in result:
            result["name"] = result["title"]
        if "originalName" in result and "filename" not in result:
            result["filename"] = result["originalName"]
        elif "name" in result and "filename" not in result:
            result["filename"] = result["name"]
        if "fileSize" in result and "file_size" not in result:
            result["file_size"] = result["fileSize"]
        if "filePath" in result and "file_path" not in result:
            result["file_path"] = result["filePath"]
        if "documentType" in result and "document_type" not in result:
            result["document_type"] = result["documentType"]

        return result

    def _find_file_on_disk(self, filename_or_path: str) -> Optional[Path]:
        """Search for a file across all candidate upload and workspace directories."""
        if not filename_or_path:
            return None
        p = Path(filename_or_path)
        if p.is_file() and p.exists():
            return p

        clean_name = p.name.lower()
        clean_stem = p.stem.lower()

        for d in CANDIDATE_SEARCH_DIRS:
            if not d.exists() or not d.is_dir():
                continue
            # Direct match
            direct = d / p.name
            if direct.is_file() and direct.exists():
                return direct

            # Search within directory (not recursing into .git or node_modules)
            try:
                for item in d.glob("*"):
                    if item.is_file():
                        item_lower = item.name.lower()
                        if item_lower == clean_name or clean_name in item_lower or clean_stem in item_lower:
                            return item
            except Exception:
                pass
        return None

    def _read_full_document_content(self, file_path_or_name: str, fallback_text: str = "") -> str:
        """Extract full document text content from disk using multi-format parser."""
        target_path = self._find_file_on_disk(file_path_or_name)
        if target_path and target_path.exists():
            try:
                from rag.parser import document_parser
                parsed = document_parser.parse_file(str(target_path))
                if parsed and parsed.text and len(parsed.text.strip()) > 0:
                    return parsed.text
            except Exception as pe:
                logger.debug(f"[DocumentStore] Parser notice for {target_path}: {pe}")
                try:
                    return target_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass
        return fallback_text

    def list_documents(
        self,
        limit: int = 50,
        search_term: Optional[str] = None,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List documents from MongoDB and candidate upload directories with RBAC visibility rules:
        - Admin sees ALL documents.
        - Non-admin sees all Admin-uploaded documents (isUploadedByAdmin: True or uploadedBy in adminIds) + their own documents.
        - Non-admin cannot see other non-admins' confidential uploads.
        """
        found_docs: Dict[str, Dict[str, Any]] = {}

        db = self._get_db()
        if db is not None:
            try:
                query: Dict[str, Any] = {}

                if not is_admin:
                    # Find all admin users so any doc uploaded by an admin user is included
                    admin_ids = []
                    try:
                        admin_users = list(db.users.find(
                            {"$or": [{"isAdmin": True}, {"role": "admin"}]},
                            {"_id": 1}
                        ))
                        admin_ids = [u["_id"] for u in admin_users]
                    except Exception:
                        pass

                    user_or_clauses: List[Dict[str, Any]] = [
                        {"isUploadedByAdmin": True},
                        {"uploaderRole": "admin"},
                        {"uploadedBy": {"$in": admin_ids}},
                        {"uploadedBy": {"$exists": False}},
                        {"uploadedBy": None}
                    ]
                    if user_id:
                        user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
                        user_or_clauses.append({"uploadedBy": user_oid})
                        user_or_clauses.append({"uploadedBy": str(user_id)})

                    query["$or"] = user_or_clauses

                if search_term and search_term.strip():
                    term = re.escape(search_term.strip())
                    term_clause = {
                        "$or": [
                            {"name": {"$regex": term, "$options": "i"}},
                            {"originalName": {"$regex": term, "$options": "i"}},
                            {"documentType": {"$regex": term, "$options": "i"}}
                        ]
                    }
                    if "$or" in query:
                        query = {"$and": [{"$or": query["$or"]}, term_clause]}
                    else:
                        query.update(term_clause)

                docs = list(db.documents.find(query).sort("createdAt", -1).limit(limit))
                for d in docs:
                    serialized = self._serialize_doc(d)
                    key = serialized.get("name") or serialized.get("originalName") or serialized.get("document_id")
                    found_docs[key] = serialized
            except Exception as e:
                logger.error(f"[DocumentStore] list_documents error: {e}")

        # Scan candidate directories for uploaded/local documents (skip phantom test files like sop_turbine.md)
        valid_extensions = {".pdf", ".docx", ".doc", ".xlsx", ".csv", ".txt", ".md", ".json"}
        for search_dir in CANDIDATE_SEARCH_DIRS:
            if not search_dir.exists() or not search_dir.is_dir():
                continue
            try:
                for file_path in search_dir.glob("*"):
                    if not file_path.is_file() or file_path.name.startswith("."):
                        continue
                    if file_path.name.lower() in ["sop_turbine.md", "powershell.cmd"]:
                        continue
                    if file_path.suffix.lower() not in valid_extensions:
                        continue
                    name = file_path.name
                    if search_term and search_term.lower() not in name.lower():
                        continue
                    # Only add if not already captured from MongoDB
                    # Non-admin users only see files explicitly registered in MongoDB with proper RBAC
                    if name not in found_docs and file_path.stem not in found_docs:
                        if not is_admin and db is not None:
                            continue
                        doc_type = file_path.suffix.lstrip(".").lower()
                        found_docs[name] = {
                            "_id": file_path.stem,
                            "document_id": file_path.stem,
                            "name": name,
                            "title": name,
                            "originalName": name,
                            "filename": name,
                            "filePath": str(file_path),
                            "file_path": str(file_path),
                            "fileSize": file_path.stat().st_size,
                            "file_size": file_path.stat().st_size,
                            "documentType": doc_type,
                            "document_type": doc_type,
                            "processingStatus": "processed",
                            "storageType": "local",
                            "isUploadedByAdmin": is_admin,
                            "metadata": {
                                "source": name,
                                "chunksCount": 1
                            }
                        }
            except Exception as scan_err:
                logger.debug(f"[DocumentStore] Disk scan note for {search_dir}: {scan_err}")

        return list(found_docs.values())[:limit]

    def get_document(
        self,
        doc_id_or_name: str,
        user_id: Optional[str] = None,
        is_admin: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Find a single document by ID, title, or filename and return complete content with RBAC check."""
        if not doc_id_or_name:
            return None

        clean_query = str(doc_id_or_name).strip()
        doc_record = None

        db = self._get_db()
        if db is not None:
            try:
                # 1. Try by ObjectId
                if ObjectId.is_valid(clean_query):
                    doc = db.documents.find_one({"_id": ObjectId(clean_query)})
                    if doc:
                        doc_record = self._serialize_doc(doc)

                # 2. Try by exact name or originalName
                if not doc_record:
                    doc = db.documents.find_one({"name": clean_query})
                    if not doc:
                        doc = db.documents.find_one({"originalName": clean_query})
                    if doc:
                        doc_record = self._serialize_doc(doc)

                # 3. Try case-insensitive regex name
                if not doc_record:
                    term = re.escape(clean_query)
                    doc = db.documents.find_one({
                        "$or": [
                            {"name": {"$regex": f"^{term}$", "$options": "i"}},
                            {"originalName": {"$regex": f"^{term}$", "$options": "i"}},
                            {"name": {"$regex": term, "$options": "i"}},
                            {"originalName": {"$regex": term, "$options": "i"}}
                        ]
                    })
                    if doc:
                        doc_record = self._serialize_doc(doc)
            except Exception as e:
                logger.error(f"[DocumentStore] get_document error: {e}")

        # Check RBAC permissions if found in MongoDB and caller is non-admin
        if doc_record and not is_admin and user_id:
            uploader = str(doc_record.get("uploadedBy", ""))
            is_doc_admin = bool(doc_record.get("isUploadedByAdmin") or doc_record.get("uploaderRole") == "admin" or not uploader)
            is_owner = (uploader == str(user_id))
            if not is_doc_admin and not is_owner:
                logger.warning(f"[DocumentStore] Access denied for user {user_id} to confidential document {doc_record.get('name')}")
                return None

        # If found in MongoDB, enrich with full un-truncated content from disk
        if doc_record:
            existing_text = doc_record.get("extractedText", "")
            file_path = doc_record.get("filePath") or doc_record.get("originalName") or doc_record.get("name")
            full_text = self._read_full_document_content(file_path, fallback_text=existing_text)
            doc_record["content"] = full_text
            doc_record["full_text"] = full_text
            if not doc_record.get("extractedText") or len(full_text) > len(existing_text):
                doc_record["extractedText"] = full_text[:4000]
            return doc_record

        # Fallback to searching physical disk in candidate directories (ignoring phantom files)
        if clean_query.lower() not in ["sop_turbine.md", "powershell.cmd"]:
            matched_file = self._find_file_on_disk(clean_query)
            if matched_file and matched_file.exists() and matched_file.name.lower() != "sop_turbine.md":
                if not is_admin and db is not None:
                    logger.warning(f"[DocumentStore] Access denied for non-admin user {user_id} to unindexed disk file {matched_file.name}")
                    return None
                full_text = self._read_full_document_content(str(matched_file))
                doc_type = matched_file.suffix.lstrip(".").lower() or "text"
                return {
                    "_id": matched_file.stem,
                    "document_id": matched_file.stem,
                    "name": matched_file.name,
                    "originalName": matched_file.name,
                    "filePath": str(matched_file),
                    "fileSize": matched_file.stat().st_size,
                    "documentType": doc_type,
                    "processingStatus": "processed",
                    "extractedText": full_text[:4000],
                    "content": full_text,
                    "full_text": full_text,
                    "isUploadedByAdmin": is_admin,
                    "storageType": "local",
                    "metadata": {
                        "source": matched_file.name,
                        "characterCount": len(full_text)
                    }
                }

        return None

    def get_document_text(
        self,
        doc_id_or_name: str,
        user_id: Optional[str] = None,
        is_admin: bool = True
    ) -> str:
        """Convenience method returning the complete un-truncated text of a document."""
        doc = self.get_document(doc_id_or_name, user_id=user_id, is_admin=is_admin)
        if not doc:
            return ""
        return doc.get("content") or doc.get("full_text") or doc.get("extractedText") or ""

    def search_documents_content(
        self,
        query: str,
        limit: int = 5,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search through all available documents (MongoDB & disk) for keywords or phrases.
        Returns matching document metadata and contextual excerpts.
        """
        results = []
        clean_q = query.strip().lower()
        if not clean_q:
            return results

        all_docs = self.list_documents(limit=50, user_id=user_id, is_admin=is_admin)
        terms = [t for t in re.split(r'\W+', clean_q) if len(t) > 2]

        for d in all_docs:
            name = d.get("name") or d.get("originalName") or ""
            full_text = self.get_document_text(name or d.get("document_id"))
            if not full_text:
                continue

            text_lower = full_text.lower()
            # Calculate match score
            score = 0
            if clean_q in text_lower:
                score += 10
            for term in terms:
                if term in text_lower:
                    score += 1

            if score > 0:
                # Find best snippet
                pos = text_lower.find(clean_q)
                if pos == -1 and terms:
                    pos = text_lower.find(terms[0])
                start_pos = max(0, pos - 150)
                end_pos = min(len(full_text), pos + 350)
                snippet = full_text[start_pos:end_pos].strip()

                results.append({
                    "document_id": d.get("document_id") or d.get("_id"),
                    "name": name,
                    "score": score,
                    "snippet": f"...{snippet}..." if start_pos > 0 else snippet,
                    "full_text": full_text,
                    "file_path": d.get("filePath")
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    async def create_document(
        self,
        name: str,
        content: str,
        document_type: str = "report",
        user_id: Optional[str] = None,
        is_admin: bool = False,
        user_role: Optional[str] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create, chunk, and index a new document into both MongoDB and Qdrant with full RBAC provenance:
        - If created by admin: isUploadedByAdmin=True (visible to all users).
        - If created by non-admin: isUploadedByAdmin=False, uploadedBy=user_id (visible to admin & author).
        """
        clean_name = name.strip()
        if not clean_name:
            clean_name = f"Document_{uuid.uuid4().hex[:8]}"

        # Save physical copy in workspace reports
        safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_name)
        if not safe_filename.endswith(".txt"):
            safe_filename += ".txt"
        file_path = DOCUMENTS_DIR / safe_filename
        file_path.write_text(content, encoding="utf-8")

        # Create MongoDB record
        doc_id = ObjectId()
        user_oid = ObjectId(user_id) if user_id and ObjectId.is_valid(user_id) else None
        db = self._get_db()

        effective_admin = is_admin
        effective_role = user_role or ("admin" if is_admin else "operator")
        effective_name = user_name or "User"
        effective_email = user_email or ""

        if db is not None:
            if user_oid:
                try:
                    u_doc = db.users.find_one({"_id": user_oid})
                    if u_doc:
                        effective_admin = bool(u_doc.get("isAdmin") or u_doc.get("role") == "admin" or is_admin)
                        effective_role = u_doc.get("role") or ("admin" if effective_admin else "operator")
                        fn = u_doc.get("fullName", {})
                        if isinstance(fn, dict):
                            effective_name = f"{fn.get('firstName', '')} {fn.get('lastName', '')}".strip() or u_doc.get("email", "User")
                        else:
                            effective_name = u_doc.get("email", "User")
                        effective_email = u_doc.get("email", "")
                except Exception as ue:
                    logger.debug(f"[DocumentStore] User lookup note: {ue}")
            elif not user_oid:
                # Default to primary admin if no user_id passed so document is a verified system asset
                try:
                    admin_doc = db.users.find_one({"$or": [{"isAdmin": True}, {"role": "admin"}]})
                    if admin_doc:
                        user_oid = admin_doc["_id"]
                        effective_admin = True
                        effective_role = "admin"
                        effective_name = "Admin (Global Asset)"
                        effective_email = admin_doc.get("email", "")
                except Exception:
                    pass

        meta = {
            "source": safe_filename,
            "document_id": str(doc_id),
            "uploaded_by": str(user_id) if user_id else (str(user_oid) if user_oid else None),
            "name": clean_name
        }

        # Chunk text
        chunks = text_chunker.chunk_text(content, base_metadata=meta)
        chunks_indexed = 0

        if chunks:
            await rag_retriever.initialize()
            texts = [c.text for c in chunks]
            metas = [c.metadata for c in chunks]
            success = await rag_retriever.add_documents(documents=texts, metadata=metas)
            if success:
                chunks_indexed = len(chunks)

        doc_record = {
            "_id": doc_id,
            "name": clean_name,
            "originalName": safe_filename,
            "mimeType": "text/plain",
            "fileSize": len(content.encode("utf-8")),
            "filePath": str(file_path),
            "storageType": "local",
            "documentType": document_type.lower(),
            "processingStatus": "processed",
            "extractedText": content[:3000],
            "isUploadedByAdmin": effective_admin,
            "uploaderRole": effective_role,
            "uploaderInfo": {
                "name": effective_name,
                "email": effective_email,
                "role": effective_role,
                "department": ""
            },
            "metadata": {
                "chunksCount": chunks_indexed,
                "characterCount": len(content),
                "source": safe_filename
            },
            "createdAt": datetime.datetime.utcnow(),
            "updatedAt": datetime.datetime.utcnow()
        }
        if user_oid:
            doc_record["uploadedBy"] = user_oid

        if db is not None:
            try:
                db.documents.insert_one(doc_record)
                logger.info(f"[DocumentStore] Created document '{clean_name}' (id={doc_id}) with {chunks_indexed} chunks in Qdrant. isUploadedByAdmin={effective_admin}")
            except Exception as me:
                logger.error(f"[DocumentStore] Failed to insert document to MongoDB: {me}")

        return {
            "success": True,
            "document_id": str(doc_id),
            "name": clean_name,
            "file_path": str(file_path),
            "chunks_indexed": chunks_indexed,
            "character_count": len(content),
            "status": "processed"
        }

    async def update_document(
        self,
        doc_id_or_name: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        append: bool = False,
        patch_target: Optional[str] = None,
        patch_replacement: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update document metadata and/or text content with re-chunking in Qdrant."""
        existing = self.get_document(doc_id_or_name)
        if not existing:
            return {"success": False, "error": f"Document '{doc_id_or_name}' not found."}

        doc_id_str = existing.get("_id") or existing.get("document_id")
        db = self._get_db()
        updates = {"updatedAt": datetime.datetime.utcnow()}

        if title and title.strip():
            updates["name"] = title.strip()

        chunks_indexed = existing.get("metadata", {}).get("chunksCount", 0)

        # Handle patch or append modifications
        existing_text = existing.get("extractedText", "")
        disk_path = existing.get("filePath")
        if disk_path and Path(disk_path).exists():
            try:
                existing_text = Path(disk_path).read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        if patch_target and patch_target in existing_text:
            content = existing_text.replace(patch_target, patch_replacement or "")
        elif append and content is not None:
            content = f"{existing_text}\n\n{content}".strip()

        if content is not None:
            # 1. Remove existing Qdrant points for this document
            await rag_retriever.delete_document(doc_id_str)

            # 2. Chunk and re-index new content
            meta = {
                "source": existing.get("originalName") or existing.get("name"),
                "document_id": doc_id_str,
                "name": updates.get("name", existing.get("name"))
            }
            chunks = text_chunker.chunk_text(content, base_metadata=meta)
            if chunks:
                await rag_retriever.initialize()
                texts = [c.text for c in chunks]
                metas = [c.metadata for c in chunks]
                success = await rag_retriever.add_documents(documents=texts, metadata=metas)
                if success:
                    chunks_indexed = len(chunks)

            updates["extractedText"] = content[:3000]
            updates["fileSize"] = len(content.encode("utf-8"))
            if "metadata" not in updates:
                updates["metadata"] = existing.get("metadata", {})
            updates["metadata"]["chunksCount"] = chunks_indexed
            updates["metadata"]["characterCount"] = len(content)

            # Update file on disk if it exists
            disk_path = existing.get("filePath")
            if disk_path and Path(disk_path).exists():
                try:
                    Path(disk_path).write_text(content, encoding="utf-8")
                except Exception as fe:
                    logger.warning(f"Could not overwrite file {disk_path}: {fe}")

        if db is not None and ObjectId.is_valid(doc_id_str):
            try:
                db.documents.update_one({"_id": ObjectId(doc_id_str)}, {"$set": updates})
                logger.info(f"[DocumentStore] Updated document '{doc_id_str}' in MongoDB and Qdrant.")
            except Exception as me:
                logger.error(f"[DocumentStore] MongoDB update error: {me}")

        return {
            "success": True,
            "document_id": doc_id_str,
            "name": updates.get("name", existing.get("name")),
            "chunks_indexed": chunks_indexed,
            "message": f"Document '{doc_id_str}' updated successfully."
        }

    async def delete_document(self, doc_id_or_name: str) -> Dict[str, Any]:
        """Delete document from MongoDB, Qdrant, and local filesystem."""
        existing = self.get_document(doc_id_or_name)
        if not existing:
            return {"success": False, "error": f"Document '{doc_id_or_name}' not found."}

        doc_id_str = existing.get("_id") or existing.get("document_id")

        # 1. Delete vector points from Qdrant
        await rag_retriever.delete_document(doc_id_str)
        if existing.get("originalName"):
            await rag_retriever.vector_db.delete_points_by_source(existing.get("originalName"))

        # 2. Delete physical file if present
        disk_path = existing.get("filePath")
        if disk_path and Path(disk_path).exists():
            try:
                Path(disk_path).unlink()
                logger.info(f"[DocumentStore] Removed file on disk: {disk_path}")
            except Exception as fe:
                logger.warning(f"Could not delete file {disk_path}: {fe}")

        # 3. Delete from MongoDB
        db = self._get_db()
        if db is not None and ObjectId.is_valid(doc_id_str):
            try:
                db.documents.delete_one({"_id": ObjectId(doc_id_str)})
                logger.info(f"[DocumentStore] Deleted document '{doc_id_str}' from MongoDB.")
            except Exception as me:
                logger.error(f"[DocumentStore] MongoDB delete error: {me}")

        return {
            "success": True,
            "document_id": doc_id_str,
            "name": existing.get("name"),
            "message": f"Document '{existing.get('name')}' successfully deleted from repository and vector index."
        }

    def sync_processed_status(
        self,
        document_id: str,
        status: str = "processed",
        chunks_count: int = 0,
        character_count: int = 0,
        extracted_text_preview: str = ""
    ) -> bool:
        """Update processing status and indexing stats in MongoDB."""
        if not document_id or not ObjectId.is_valid(document_id):
            return False

        db = self._get_db()
        if db is None:
            return False

        try:
            update_data = {
                "processingStatus": status,
                "updatedAt": datetime.datetime.utcnow()
            }
            if extracted_text_preview:
                update_data["extractedText"] = extracted_text_preview[:4000]
            if chunks_count > 0 or character_count > 0:
                update_data["metadata.chunksCount"] = chunks_count
                update_data["metadata.characterCount"] = character_count

            db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_data}
            )
            logger.info(f"[DocumentStore] Synced status for document {document_id}: status={status}, chunks={chunks_count}")
            return True
        except Exception as e:
            logger.error(f"[DocumentStore] sync_processed_status error: {e}")
            return False


document_store = DocumentStore()
