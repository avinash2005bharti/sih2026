"""
RAG Knowledge Base search and indexing tools for Sovereign AI Workbench.
Connects agents to the sovereign Qdrant vector database to store and retrieve confidential documentation.
"""

from typing import Any, Dict, List, Optional
from tools.base_tool import BaseTool
from rag.retriever import rag_retriever
from rag.embeddings import embeddings_service
from rag.qdrant_client import QdrantClient
from core.config import settings
from core.logging import logger


class KnowledgeSearchTool(BaseTool):
    """Searches indexed documents in the sovereign vector database."""

    name = "search_knowledge_base"
    description = (
        "Search indexed sovereign technical documentation, manuals, incident reports, and regulations "
        "using semantic vector search. Returns the most relevant excerpts with similarity scores."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language question or search topic (e.g. 'bearing replacement procedure', 'vibration tolerance standard')"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of relevant document chunks to return (default 4)"
            }
        },
        "required": ["query"]
    }

    async def arun(self, query: str, top_k: int = 4, **kwargs) -> Dict[str, Any]:
        try:
            logger.info(f"KnowledgeSearchTool querying: '{query}' (top_k={top_k})")

            try:
                initialized = await rag_retriever.initialize()
            except Exception as init_err:
                logger.warning(f"RAG initialize failed: {init_err}")
                initialized = False

            if not initialized:
                return {
                    "success": False,
                    "error": "Sovereign vector database (Qdrant) is currently unavailable or initializing.",
                    "results": []
                }

            results = await rag_retriever.retrieve(query=query, top_k=top_k)

            formatted = []
            for r in results:
                formatted.append({
                    "score": round(r.get("score", 0.0), 4),
                    "text": r.get("text", "").strip(),
                    "source": r.get("metadata", {}).get("source", "unknown")
                })

            return {
                "success": True,
                "query": query,
                "total_found": len(formatted),
                "results": formatted
            }
        except Exception as e:
            logger.error(f"KnowledgeSearchTool error: {e}")
            return {"success": False, "error": str(e), "results": []}


class IndexDocumentTool(BaseTool):
    """Indexes text or notes into the sovereign Qdrant vector database."""

    name = "index_document"
    description = (
        "Index text or notes into the sovereign vector database so it can be retrieved later using semantic search."
    )
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title or reference name of the document"
            },
            "content": {
                "type": "string",
                "description": "Text content to embed and index"
            }
        },
        "required": ["title", "content"]
    }

    async def arun(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            vector = await embeddings_service.get_embedding(content)
            if not vector:
                return {"success": False, "error": "Failed to generate embedding from local model"}

            client = QdrantClient()
            await client.create_collection()
            point_id = abs(hash(f"{title}_{content[:50]}")) % (10**9)

            success = await client.upsert_points([{
                "id": point_id,
                "vector": vector,
                "payload": {
                    "title": title,
                    "text": content,
                    "source": title
                }
            }])

            return {
                "success": success,
                "title": title,
                "point_id": point_id,
                "message": f"Document '{title}' successfully indexed into sovereign vector store."
            }
        except Exception as e:
            logger.error(f"IndexDocumentTool error: {e}")
            return {"success": False, "error": str(e)}
