"""
RAG Retriever for Sovereign AI Workbench.
Connects embeddings generation, Qdrant vector storage, verified point insertion, and metadata-filtered search.
"""

from typing import List, Dict, Optional, Any
import uuid
import datetime
from rag.embeddings import embeddings_service
from rag.qdrant_client import qdrant_client
from core.logging import logger
from core.config import settings


class RAGRetriever:
    """Retrieves relevant document chunks using local embeddings and verified Qdrant vector search."""

    def __init__(self):
        self.embeddings_service = embeddings_service
        self.vector_db = qdrant_client
        logger.info("[RAG] Initialized RAG retriever")

    async def initialize(self) -> bool:
        """Initialize and validate Qdrant collection with the correct vector dimension."""
        try:
            if not await self.vector_db.health_check():
                logger.error("[QDRANT] Qdrant is not accessible")
                return False

            dim = await self.embeddings_service.detect_dimension()
            if not await self.vector_db.create_collection(vector_size=dim):
                logger.error(f"[QDRANT] Failed to initialize collection '{self.vector_db.collection}'")
                return False

            logger.info(f"[RAG] Vector collection '{self.vector_db.collection}' ready (dimension={dim})")
            return True

        except Exception as e:
            logger.error(f"[RAG] Initialization error: {e}", exc_info=True)
            return False

    async def add_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Embed, index, and verify documents in Qdrant vector store.
        Fails explicitly if embedding fails, upsert fails, or post-upsert verification fails.
        """
        if not documents:
            logger.warning("[RAG] No documents provided to add_documents")
            return False

        try:
            logger.info(f"[INGEST] Processing {len(documents)} document chunks for vector indexing")
            if not await self.initialize():
                raise ConnectionError("Qdrant collection initialization failed")

            # 1. Generate and validate embeddings
            embeddings = await self.embeddings_service.embed_texts(documents)
            if not embeddings or len(embeddings) != len(documents):
                raise RuntimeError(f"Embedding count mismatch: expected {len(documents)}, got {len(embeddings) if embeddings else 0}")

            # 2. Build verified Qdrant points with standard payload schema
            points = []
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            first_doc_id = None

            for i, (doc_text, embedding) in enumerate(zip(documents, embeddings)):
                meta = metadata[i] if metadata and i < len(metadata) else {}
                doc_id = str(meta.get("document_id") or meta.get("doc_id") or uuid.uuid4().hex)
                if not first_doc_id:
                    first_doc_id = doc_id

                filename = str(meta.get("filename") or meta.get("source") or meta.get("name") or "document")
                chunk_id = str(meta.get("chunk_id") or f"{doc_id}_chunk_{i}")
                page_num = meta.get("page", 1)
                user_id = str(meta.get("uploaded_by") or meta.get("user_id") or "system")
                doc_type = str(meta.get("document_type") or "text")

                payload = {
                    "document_id": doc_id,
                    "filename": filename,
                    "chunk_id": chunk_id,
                    "text": doc_text,
                    "page": page_num,
                    "source": filename,
                    "user_id": user_id,
                    "created_at": meta.get("created_at") or now_iso,
                    "document_type": doc_type,
                    "doc_index": i,
                    "metadata": meta
                }

                point = {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": payload
                }
                points.append(point)

            # 3. Synchronously upsert points
            upsert_ok = await self.vector_db.upsert_points(points, wait=True)
            if not upsert_ok:
                raise RuntimeError(f"Failed to upsert {len(points)} points into Qdrant collection '{self.vector_db.collection}'")

            # 4. Mandatory post-upsert verification: verify point count and retrieve sample point
            verify_res = await self.vector_db.verify_ingestion(
                document_id=first_doc_id,
                expected_min_chunks=len(points)
            )

            if not verify_res.get("verified"):
                raise RuntimeError(
                    f"[VERIFY] Ingestion verification failed for document_id={first_doc_id}: "
                    f"points_count={verify_res.get('points_count')}, sample_found={verify_res.get('sample_point_found')}"
                )

            logger.info(
                f"[INGEST] status=COMPLETE document_id={first_doc_id} points_verified={verify_res.get('points_count')}"
            )
            return True

        except Exception as e:
            logger.error(f"[INGEST] Ingestion failure: {e}", exc_info=True)
            raise

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: float = 0.0,
        document_id: Optional[str] = None,
        allowed_doc_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Evidence-grounded vector similarity search.
        Returns top-k relevant chunks with similarity scores and full provenance metadata.
        Respects RBAC: if is_admin is False, only documents in allowed_doc_ids or visible to user_id are returned.
        """
        k = top_k or getattr(settings, "RAG_TOP_K", 5)
        formatted_results = []
        try:
            # Resolve allowed document IDs for non-admin users if not explicitly passed
            effective_allowed_ids = allowed_doc_ids
            if not is_admin and effective_allowed_ids is None and user_id:
                try:
                    from rag.document_store import document_store
                    accessible_docs = document_store.list_documents(user_id=user_id, is_admin=False, limit=500)
                    effective_allowed_ids = [
                        str(d.get("document_id") or d.get("_id") or d.get("id"))
                        for d in accessible_docs
                        if d.get("document_id") or d.get("_id") or d.get("id")
                    ]
                except Exception as doc_err:
                    logger.warning(f"[RAG] Failed to resolve accessible documents for user {user_id}: {doc_err}")

            # If user is non-admin and has no accessible documents, return empty
            if not is_admin and effective_allowed_ids is not None and len(effective_allowed_ids) == 0:
                logger.info(f"[RAG] User {user_id} has 0 accessible documents. Skipping vector retrieval.")
                return []

            query_embedding = await self.embeddings_service.embed_text(query)
            if query_embedding:
                filter_dict = None
                if document_id:
                    filter_dict = {
                        "must": [{"key": "document_id", "match": {"value": str(document_id)}}]
                    }
                elif effective_allowed_ids is not None:
                    filter_dict = {
                        "must": [{"key": "document_id", "match": {"any": [str(x) for x in effective_allowed_ids]}}]
                    }

                results = await self.vector_db.search(
                    query_vector=query_embedding,
                    limit=k,
                    score_threshold=score_threshold,
                    filter_dict=filter_dict
                )

                for r in results:
                    payload = r.get("payload", {})
                    score = round(float(r.get("score", 0.0)), 4)
                    formatted_results.append({
                        "document_id": payload.get("document_id", ""),
                        "chunk_id": payload.get("chunk_id", ""),
                        "filename": payload.get("filename", payload.get("source", "document")),
                        "page": payload.get("page", 1),
                        "text": payload.get("text", ""),
                        "similarity_score": score,
                        "score": score,
                        "metadata": payload.get("metadata", {})
                    })

                logger.info(f"[RAG] Retrieved {len(formatted_results)} evidence chunks for query='{query[:50]}' (top_k={k})")
            else:
                logger.info(f"[RAG] Vector embedding unavailable for '{query[:50]}', falling back to document text search")

        except Exception as e:
            logger.error(f"[RAG] Vector search error: {e}")
            formatted_results = []

        # Hybrid Fallback: Search document store and local repository files if vector results are empty
        if not formatted_results:
            try:
                from rag.document_store import document_store
                text_matches = document_store.search_documents_content(
                    query,
                    limit=k,
                    user_id=user_id,
                    is_admin=is_admin
                )
                for idx, m in enumerate(text_matches, start=1):
                    formatted_results.append({
                        "document_id": m.get("document_id", ""),
                        "chunk_id": f"chunk_{idx}",
                        "filename": m.get("name", "document"),
                        "page": 1,
                        "text": m.get("snippet", ""),
                        "similarity_score": round(min(0.95, 0.5 + (m.get("score", 1) * 0.05)), 4),
                        "score": round(min(0.95, 0.5 + (m.get("score", 1) * 0.05)), 4),
                        "metadata": {"source": m.get("name"), "full_text": m.get("full_text", "")}
                    })
                if formatted_results:
                    logger.info(f"[RAG] Hybrid fallback search retrieved {len(formatted_results)} matches for '{query[:50]}'")
            except Exception as fe:
                logger.debug(f"[RAG] Hybrid fallback note: {fe}")

        return formatted_results

    def build_context_block(self, chunks: List[Dict[str, Any]]) -> str:
        """Compresses retrieved chunks into an evidence block with exact citations."""
        if not chunks:
            return "No relevant information was found in the indexed knowledge base."

        blocks = []
        for i, c in enumerate(chunks, 1):
            filename = c.get("filename", "document")
            page = c.get("page", 1)
            doc_id = c.get("document_id", "")
            chunk_id = c.get("chunk_id", "")
            score = c.get("similarity_score", 0.0)
            text = c.get("text", "").strip()

            blocks.append(
                f"[Source: {filename} | Page: {page} | Chunk: {chunk_id} | Score: {score}]\n{text}"
            )

        return "\n\n---\n\n".join(blocks)

    async def delete_document(self, document_id: str) -> bool:
        """Delete all points belonging to a specific document_id."""
        return await self.vector_db.delete_points_by_document_id(document_id)

    async def clear(self) -> bool:
        """Clear all indexed documents."""
        return await self.vector_db.delete_collection()


# Global singleton retriever
rag_retriever = RAGRetriever()

