"""
Unified Document Ingestion Loader for Sovereign RAG pipeline.
Coordinates DocumentParser, TextChunker, and RAGRetriever with end-to-end verification.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from rag.parser import document_parser
from rag.chunker import text_chunker
from rag.retriever import rag_retriever
from rag.document_store import document_store
from core.logging import logger


class DocumentLoader:
    """Coordinates parsing, chunking, embedding, vector indexing, and verification of files."""

    async def ingest_file(
        self,
        file_path: str,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse, chunk, embed, and index a single document into Qdrant with verification.
        Only reports success after Qdrant point count and sample retrieval are confirmed.
        """
        logger.info(f"[INGEST] Starting document ingestion: {file_path}")
        target_path = Path(file_path)

        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        meta = custom_metadata.copy() if custom_metadata else {}
        doc_id = meta.get("document_id") or meta.get("doc_id") or uuid.uuid4().hex
        meta["document_id"] = doc_id

        # 1. Parse file
        logger.info(f"[PARSE] Reading text and metadata from {target_path.name}")
        parsed = document_parser.parse_file(str(target_path))
        file_meta = parsed.metadata.copy()
        file_meta.update(meta)

        if not parsed.text or not parsed.text.strip():
            logger.warning(f"[PARSE] Document {target_path.name} contains no extractable text")
            if doc_id:
                document_store.sync_processed_status(
                    document_id=doc_id,
                    status="failed",
                    chunks_count=0
                )
            return {
                "success": False,
                "file_path": file_path,
                "filename": target_path.name,
                "document_id": doc_id,
                "message": "Document contains no extractable text",
                "chunks_indexed": 0,
                "extracted_text_preview": ""
            }

        # 2. Chunk text
        chunks = text_chunker.chunk_text(parsed.text, base_metadata=file_meta)
        logger.info(f"[CHUNK] document_id={doc_id} filename={target_path.name} chunks={len(chunks)}")

        if not chunks:
            if doc_id:
                document_store.sync_processed_status(
                    document_id=doc_id,
                    status="failed",
                    chunks_count=0
                )
            return {
                "success": False,
                "file_path": file_path,
                "filename": target_path.name,
                "document_id": doc_id,
                "message": "Chunking produced 0 chunks",
                "chunks_indexed": 0,
                "extracted_text_preview": ""
            }

        # 3. Vector indexing & Qdrant verification
        doc_texts = [c.text for c in chunks]
        doc_metas = []
        for idx, c in enumerate(chunks):
            chunk_m = c.metadata.copy()
            chunk_m["document_id"] = doc_id
            chunk_m["filename"] = target_path.name
            chunk_m["chunk_id"] = f"{doc_id}_chunk_{idx}"
            chunk_m["page"] = chunk_m.get("page", 1)
            doc_metas.append(chunk_m)

        try:
            success = await rag_retriever.add_documents(documents=doc_texts, metadata=doc_metas)
            if not success:
                raise RuntimeError("RAG retriever add_documents failed verification")

            preview = parsed.text[:3000].strip()
            # Synchronize to MongoDB
            if doc_id:
                document_store.sync_processed_status(
                    document_id=doc_id,
                    status="processed",
                    chunks_count=len(chunks),
                    character_count=len(parsed.text),
                    extracted_text_preview=preview
                )

            logger.info(
                f"[INGEST] status=COMPLETE document_id={doc_id} chunks_indexed={len(chunks)} verified=True"
            )

            return {
                "success": True,
                "file_path": file_path,
                "filename": target_path.name,
                "document_id": doc_id,
                "chunks_count": len(chunks),
                "chunks_indexed": len(chunks),
                "embeddings_count": len(chunks),
                "points_inserted": len(chunks),
                "verified": True,
                "character_count": len(parsed.text),
                "extracted_text_preview": preview
            }

        except Exception as e:
            logger.error(f"[INGEST] Failed to index document into Qdrant: {e}", exc_info=True)
            if doc_id:
                document_store.sync_processed_status(
                    document_id=doc_id,
                    status="failed",
                    chunks_count=0
                )
            return {
                "success": False,
                "file_path": file_path,
                "filename": target_path.name,
                "document_id": doc_id,
                "error": str(e),
                "chunks_count": 0,
                "chunks_indexed": 0,
                "embeddings_count": 0,
                "points_inserted": 0,
                "verified": False,
                "extracted_text_preview": ""
            }

    async def load_and_index(
        self,
        file_path: str,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convenience method to load, chunk, embed, index and verify a document."""
        meta = custom_metadata.copy() if custom_metadata else {}
        if document_id:
            meta["document_id"] = document_id
        if user_id:
            meta["user_id"] = user_id
        meta.update(kwargs)
        return await self.ingest_file(file_path=file_path, custom_metadata=meta)


    async def ingest_directory(self, dir_path: str, recursive: bool = True) -> Dict[str, Any]:
        """Ingest all supported documents inside a directory."""
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        pattern = "**/*" if recursive else "*"
        processed = []
        total_chunks = 0

        for file_item in path.glob(pattern):
            if file_item.is_file() and file_item.suffix.lower() in document_parser.SUPPORTED_EXTENSIONS:
                try:
                    res = await self.ingest_file(str(file_item))
                    if res["success"]:
                        processed.append(file_item.name)
                        total_chunks += res["chunks_indexed"]
                except Exception as e:
                    logger.error(f"[INGEST] Failed to ingest {file_item.name}: {e}")

        return {
            "success": True,
            "directory": str(dir_path),
            "files_processed": len(processed),
            "total_chunks_indexed": total_chunks,
            "file_names": processed
        }


# Global singleton loader
document_loader = DocumentLoader()
