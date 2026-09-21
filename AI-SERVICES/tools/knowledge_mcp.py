"""
Knowledge MCP Tools for Sovereign AI Workbench.
Connects vector and knowledge search to RAG retriever and Qdrant.
"""

from typing import Any, Dict
from rag.retriever import rag_retriever
from core.logging import logger


async def vector_search(query: str = "", top_k: int = 5, **kwargs) -> Dict[str, Any]:
    """Semantic vector search across indexed documents in Qdrant."""
    try:
        await rag_retriever.initialize()
        results = await rag_retriever.retrieve(query=query, top_k=top_k)
        return {
            "success": True,
            "query": query,
            "total_found": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"vector_search error: {e}")
        return {"success": False, "error": str(e), "results": []}


async def graph_search(query: str = "", **kwargs) -> Dict[str, Any]:
    """Graph search across entities and task relations."""
    try:
        from memory.graph.neo4j_service import neo4j_service
        res = await neo4j_service.search(query=query)
        return {"success": True, "graph_results": res}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def hybrid_search(query: str = "", top_k: int = 5, **kwargs) -> Dict[str, Any]:
    """Hybrid search combining vector similarity and keyword relevance."""
    return await vector_search(query=query, top_k=top_k, **kwargs)


async def retrieve_context(query: str = "", top_k: int = 4, **kwargs) -> Dict[str, Any]:
    """Retrieve synthesized context from technical documents."""
    try:
        await rag_retriever.initialize()
        results = await rag_retriever.retrieve(query=query, top_k=top_k)
        context_snippets = [
            f"[{r.get('source', 'doc')} (score {r.get('score', 0):.2f})]: {r.get('text', '')}"
            for r in results
        ]
        return {
            "success": True,
            "context": "\n\n".join(context_snippets),
            "raw_results": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


knowledge_mcp_tools = {
    "knowledge.vector_search": vector_search,
    "knowledge.graph_search": graph_search,
    "knowledge.hybrid_search": hybrid_search,
    "knowledge.retrieve_context": retrieve_context
}
