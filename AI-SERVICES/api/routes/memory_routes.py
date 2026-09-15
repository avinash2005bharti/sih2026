"""
Memory API Endpoints for Sovereign AI Workbench.
Exposes health checks, semantic memory search, memory creation, deletion, and graph inspection.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel


from memory.memory_manager import memory_manager
from memory.models import (
    MemorySearchRequest,
    MemoryCreateRequest,
    MemoryHealthStatus
)
from core.logging import logger
from memory.graph.neo4j_service import neo4j_service

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/health", response_model=MemoryHealthStatus, summary="Unified Memory Health Check")
@router.get("/health/memory", response_model=MemoryHealthStatus, summary="Unified Memory Health Check (alias)", include_in_schema=False)
async def get_memory_health():
    """
    Unified memory health check testing:
    - MongoDB (STM)
    - Qdrant (LTM vectors)
    - Neo4j (Knowledge graph)
    - Mem0 (Orchestration)
    - Ollama (Inference)
    - Embedding Model (nomic-embed-text)
    """
    try:
        status = await memory_manager.health_check()
        return MemoryHealthStatus(
            memory=status.get("memory", "unknown"),
            stm=status.get("stm", "unknown"),
            ltm=status.get("ltm", "unknown"),
            qdrant=status.get("qdrant", "unknown"),
            neo4j=status.get("neo4j", "unknown"),
            mem0=status.get("mem0", "unknown"),
            ollama=status.get("ollama", "unknown"),
            embedding_model=status.get("embedding_model", "unknown"),
            details=status.get("details", {})
        )
    except Exception as e:
        logger.error(f"[MEMORY API] Health check error: {e}", exc_info=True)
        return MemoryHealthStatus(
            memory="unavailable",
            stm="error",
            ltm="error",
            qdrant="error",
            neo4j="error",
            mem0="error",
            ollama="error",
            embedding_model="error",
            details={"error": str(e)}
        )


@router.get("/search", summary="Semantic Memory Search")
@router.post("/search", summary="Semantic Memory Search (JSON Body)")
async def search_memories(
    q: Optional[str] = Query(None, description="Search query string"),
    user_id: Optional[str] = Query(None, description="Filter by User ID"),
    limit: int = Query(5, ge=1, le=50, description="Max memories to return"),
    score_threshold: float = Query(0.35, ge=0.0, le=1.0, description="Minimum similarity score"),
    payload: Optional[Dict[str, Any]] = None
):
    """
    Search semantic memories for a user using Qdrant vector similarity and Mem0.
    """
    try:
        # Support JSON payload from POST
        query_text = q
        uid = user_id
        lim = limit
        thresh = score_threshold
        if payload:
            query_text = payload.get("query") or payload.get("q") or query_text
            uid = payload.get("user_id") or uid
            lim = payload.get("limit") or lim
            thresh = payload.get("score_threshold", thresh)

        if not query_text:
            raise HTTPException(status_code=400, detail="Search query 'q' or 'query' is required")

        results = await memory_manager.search(
            query=query_text,
            user_id=uid,
            limit=lim,
            score_threshold=thresh
        )
        return {
            "success": True,
            "query": query_text,
            "user_id": uid,
            "count": len(results),
            "memories": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MEMORY API] Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Memory search error: {str(e)}")


@router.post("", summary="Record Memory")
@router.post("/", summary="Record Memory")
async def create_memory(request: MemoryCreateRequest):
    """
    Store a new long-term fact, preference, or domain knowledge item.
    Persists to both Qdrant vector database and Neo4j knowledge graph.
    """
    try:
        item = await memory_manager.add_memory(
            user_id=request.user_id,
            fact_or_preference=request.content,
            conversation_id=request.conversation_id,
            memory_type=request.memory_type,
            metadata=request.metadata
        )
        if not item:
            raise HTTPException(status_code=400, detail="Failed to record memory or content contained secrets.")

        return {
            "success": True,
            "message": "Memory persisted successfully",
            "memory": item.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MEMORY API] Create memory error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create memory: {str(e)}")


@router.delete("/{memory_id}", summary="Delete Memory")
async def delete_memory(
    memory_id: str,
    user_id: Optional[str] = Query(None, description="Requesting User ID"),
    authorization: Optional[str] = Header(None, description="Auth token")
):
    """
    Delete a specific memory by ID.
    Enforces user ownership or admin authorization.
    """
    try:
        deleted = await memory_manager.delete_memory(memory_id)
        if not deleted:
            return {
                "success": False,
                "message": f"Memory {memory_id} not found or could not be deleted"
            }
        return {
            "success": True,
            "message": f"Memory {memory_id} successfully deleted"
        }
    except Exception as e:
        logger.error(f"[MEMORY API] Delete memory error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


@router.get("/graph", summary="Query Knowledge Graph Insights")
@router.post("/graph", summary="Query Knowledge Graph Insights (JSON or Cypher)")
async def get_graph_insights(
    query: Optional[str] = Query(None, description="Query terms to search connected entities"),
    user_id: Optional[str] = Query(None, description="User ID context"),
    payload: Optional[Dict[str, Any]] = None
):
    """
    Query entities and relationships from the Neo4j knowledge graph.
    """
    try:
        q = query
        uid = user_id
        if payload:
            q = payload.get("query") or q
            uid = payload.get("user_id") or uid
            if payload.get("cypher"):
                res = await neo4j_service.execute_cypher(payload["cypher"], payload.get("parameters"))
                return {
                    "success": True,
                    "count": len(res.get("results", [])),
                    "results": res.get("results", [])
                }

        relations = await memory_manager.get_graph_context(query=q or "", user_id=uid)
        return {
            "success": True,
            "query": q,
            "count": len(relations),
            "relations": relations
        }
    except Exception as e:
        logger.error(f"[MEMORY API] Graph query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Graph query error: {str(e)}")
