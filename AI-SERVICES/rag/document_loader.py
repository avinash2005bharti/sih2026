"""
Unified Document Ingestion Loader for Sovereign RAG pipeline.
Coordinates DocumentParser, TextChunker, and RAGRetriever to index files into Qdrant.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from rag.parser import document_parser
from rag.chunker import text_chunker
from rag.retriever import rag_retriever
from core.logging import logger


class DocumentLoader:
    """Coordinates parsing, chunking, and vector indexing of files."""

    async def ingest_file(self, file_path: str, custom_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse, chunk, and index a single document into Qdrant.
        """
        logger.info(f"Ingesting document for RAG: {file_path}")

        # 1. Parse file
        parsed = document_parser.parse_file(file_path)
        meta = parsed.metadata.copy()
        if custom_metadata:
            meta.update(custom_metadata)

        # 2. Chunk text
        chunks = text_chunker.chunk_text(parsed.text, base_metadata=meta)
        if not chunks:
            return {
                "success": False,
                "file_path": file_path,
                "message": "Document contains no extractable text",
                "chunks_indexed": 0
            }

        # 3. Ensure retriever is initialized
        await rag_retriever.initialize()

        # 4. Ingest into Qdrant
        doc_texts = [c.text for c in chunks]
        doc_metas = [c.metadata for c in chunks]

        success = await rag_retriever.add_documents(documents=doc_texts, metadata=doc_metas)

        logger.info(f"Ingested {len(chunks)} chunks from {file_path} into sovereign vector database.")
        return {
            "success": success,
            "file_path": file_path,
            "filename": parsed.metadata.get("source"),
            "chunks_indexed": len(chunks),
            "character_count": len(parsed.text)
        }

    async def ingest_directory(self, dir_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Ingest all supported documents inside a directory.
        """
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
                    logger.error(f"Failed to ingest {file_item.name}: {e}")

        return {
            "success": True,
            "directory": str(dir_path),
            "files_processed": len(processed),
            "total_chunks_indexed": total_chunks,
            "file_names": processed
        }


document_loader = DocumentLoader()
