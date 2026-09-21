"""
API routes for document management and RAG.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import os
import uuid
from rag.retriever import rag_retriever
from rag.document_loader import document_loader
from core.logging import logger

router = APIRouter(prefix="/api")

# Maximum file size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".json"}


class DocumentRequest(BaseModel):
    """Request to add documents to RAG."""
    documents: List[str] = Field(..., description="List of document texts to index")
    metadata: Optional[List[dict]] = Field(None, description="Optional metadata for each document")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    "Your maintenance report content here",
                    "Another document content"
                ],
                "metadata": [
                    {"source": "report1.txt", "date": "2026-09-11"},
                    {"source": "report2.txt", "date": "2026-09-10"}
                ]
            }
        }
    )


class DocumentResponse(BaseModel):
    """Response after adding documents."""
    success: bool
    message: str
    documents_indexed: int


class SearchRequest(BaseModel):
    """Request to search documents."""
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    score_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity score")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "maintenance issues",
                "top_k": 5,
                "score_threshold": 0.0
            }
        }
    )


class SearchResult(BaseModel):
    """Single search result."""
    score: float
    text: str
    metadata: dict


class SearchResponse(BaseModel):
    """Response from document search."""
    query: str
    results: List[SearchResult]
    count: int


class RagStatusResponse(BaseModel):
    """RAG system status."""
    status: str
    qdrant_connected: bool
    message: str


@router.post("/documents", response_model=DocumentResponse, summary="Index documents for RAG")
async def index_documents(request: DocumentRequest):
    """
    Add documents to the RAG system for retrieval.

    - **documents**: List of document texts to index
    - **metadata**: Optional metadata dict for each document

    Returns count of successfully indexed documents.
    """
    try:
        # Initialize RAG if not already done
        if not await rag_retriever.initialize():
            raise HTTPException(status_code=502, detail="RAG system not available")

        # Add documents
        success = await rag_retriever.add_documents(
            request.documents,
            request.metadata
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to index documents")

        return DocumentResponse(
            success=True,
            message=f"Successfully indexed {len(request.documents)} documents",
            documents_indexed=len(request.documents)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/documents/search", response_model=SearchResponse, summary="Search documents")
async def search_documents(request: SearchRequest):
    """
    Search for relevant documents in the RAG system.

    - **query**: Search query text
    - **top_k**: Number of results to return (1-20)
    - **score_threshold**: Minimum similarity score (0-1)

    Returns most similar documents with similarity scores.
    """
    try:
        logger.info(f"Document search | query='{request.query}' | top_k={request.top_k}")

        # Initialize RAG if needed
        if not await rag_retriever.initialize():
            raise HTTPException(status_code=502, detail="RAG system not available")

        # Retrieve documents
        results = await rag_retriever.retrieve(
            request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold
        )

        # Format response
        search_results = [
            SearchResult(
                score=result["score"],
                text=result["text"],
                metadata=result["metadata"]
            )
            for result in results
        ]

        logger.info(f"Search returned {len(search_results)} results")

        return SearchResponse(
            query=request.query,
            results=search_results,
            count=len(search_results)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/documents/rag-status", response_model=RagStatusResponse, summary="RAG system status")
async def rag_status():
    """
    Get status of the RAG system.

    Returns Qdrant connectivity and system health.
    """
    try:
        # Check Qdrant connectivity
        qdrant_ok = await rag_retriever.vector_db.health_check()

        status = "healthy" if qdrant_ok else "degraded"
        message = "RAG system is ready" if qdrant_ok else "Vector database not accessible"

        return RagStatusResponse(
            status=status,
            qdrant_connected=qdrant_ok,
            message=message
        )

    except Exception as e:
        logger.error(f"Error checking RAG status: {e}")
        return RagStatusResponse(
            status="error",
            qdrant_connected=False,
            message=f"Error: {str(e)}"
        )


@router.delete("/documents/clear", summary="Clear all indexed documents")
async def clear_documents():
    """
    Clear all documents from the RAG system.

    WARNING: This permanently deletes all indexed documents.
    """
    try:
        logger.warning("Clearing all documents from RAG")

        success = await rag_retriever.clear()

        if success:
            return {"status": "cleared", "message": "All documents cleared"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear documents")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


from rag.document_store import document_store
import shutil
from pathlib import Path

UPLOAD_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
UPLOAD_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ProcessDocumentRequest(BaseModel):
    filePath: str = Field(..., description="File path on disk to parse and ingest")
    documentId: Optional[str] = Field(None, description="Document ID in MongoDB")
    userId: Optional[str] = Field(None, description="User ID uploading document")
    name: Optional[str] = Field(None, description="Optional document name")


@router.get("/documents", summary="List all indexed documents")
async def list_documents_route(
    limit: int = 50,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    is_admin: bool = False
):
    """List all documents in the repository adhering to RBAC visibility rules."""
    try:
        docs = document_store.list_documents(limit=limit, search_term=search, user_id=user_id, is_admin=is_admin)
        return {
            "success": True,
            "count": len(docs),
            "documents": docs
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", summary="Get document by ID or name")
async def get_document_route(
    document_id: str,
    user_id: Optional[str] = None,
    is_admin: bool = False
):
    """Retrieve details for a single document with RBAC permission check."""
    doc = document_store.get_document(document_id, user_id=user_id, is_admin=is_admin)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found or access denied.")
    return {
        "success": True,
        "document": doc
    }


@router.post("/documents/process", summary="Process and index a document file")
async def process_document(request: ProcessDocumentRequest):
    """
    Process and ingest a document file into the sovereign vector database.
    Called by Node.js backend when a document is uploaded.
    """
    try:
        logger.info(f"Processing document for indexing: {request.filePath} (docId: {request.documentId})")
        custom_meta = {
            "document_id": request.documentId,
            "uploaded_by": request.userId,
            "name": request.name
        }

        # Resolve path safely
        target_path = Path(request.filePath)
        if not target_path.exists():
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            clean_req = request.filePath.lstrip("/\\")
            candidates = [
                repo_root / clean_req,
                repo_root / "BACKEND" / clean_req,
                repo_root / "BACKEND" / "uploads" / "documents" / target_path.name,
                UPLOAD_CACHE_DIR / target_path.name,
                repo_root / "AI-SERVICES" / "workspace" / "reports" / target_path.name,
            ]
            found = None
            for c in candidates:
                if c.exists():
                    found = c
                    break
            if found:
                target_path = found
            else:
                raise FileNotFoundError(f"File not found: {request.filePath}")

        result = await document_loader.ingest_file(
            file_path=str(target_path),
            custom_metadata=custom_meta
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=f"Document indexing failed: {result.get('error') or result.get('message')}")

        return {
            "success": True,
            "message": f"Document processed, indexed, and verified into {result.get('chunks_indexed', 0)} chunks.",
            "details": result
        }
    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        if request.documentId:
            document_store.sync_processed_status(
                document_id=request.documentId,
                status="failed",
                chunks_count=0
            )
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.post("/documents/upload", summary="Upload, chunk, and index a document file")
async def upload_document_route(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    documentId: Optional[str] = Form(None),
    userId: Optional[str] = Form(None),
    documentType: Optional[str] = Form("pdf")
):
    """
    Direct multipart file upload to AI service.
    Saves file to disk, chunks, embeds into Qdrant, and synchronizes to MongoDB.
    """
    try:
        original_name = file.filename or "uploaded_document"
        clean_ext = Path(original_name).suffix
        stored_name = f"{uuid.uuid4().hex}_{original_name}"
        dest = UPLOAD_CACHE_DIR / stored_name

        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc_name = name or Path(original_name).stem
        custom_meta = {
            "document_id": documentId,
            "uploaded_by": userId,
            "name": doc_name,
            "source": original_name
        }

        result = await document_loader.ingest_file(
            file_path=str(dest),
            custom_metadata=custom_meta
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=f"Upload indexing failed: {result.get('error') or result.get('message')}")

        return {
            "success": True,
            "message": f"Document '{doc_name}' uploaded and verified into {result.get('chunks_indexed', 0)} chunks.",
            "file_path": str(dest),
            "original_name": original_name,
            "details": result
        }
    except Exception as e:
        logger.error(f"Upload and indexing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@router.delete("/documents/{document_id}", summary="Delete document from repository and Qdrant")
async def delete_document_route(document_id: str):
    """Delete document by ID from MongoDB, local disk, and Qdrant vector store."""
    try:
        result = await document_store.delete_document(document_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


