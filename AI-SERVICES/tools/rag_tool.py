import json
from typing import Any, Dict, List, Optional
from tools.base_tool import BaseTool
from rag.retriever import rag_retriever
from rag.embeddings import embeddings_service
from rag.qdrant_client import qdrant_client
from core.config import settings
from core.logging import logger
from langchain_core.tools import tool


class KnowledgeSearchTool(BaseTool):
    name = "search_knowledge_base"
    description = "Search indexed sovereign technical documentation, manuals, incident reports, and regulations using semantic vector search."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query or semantic concept"},
            "top_k": {"type": "integer", "description": "Number of results to retrieve"}
        },
        "required": ["query"]
    }

    async def arun(self, query: str, top_k: int = 4, **kwargs) -> str:
        try:
            logger.info(f"KnowledgeSearchTool querying: '{query}' (top_k={top_k})")
            
            try:
                initialized = await rag_retriever.initialize()
            except Exception as init_err:
                logger.warning(f"RAG initialize failed: {init_err}")
                initialized = False

            if not initialized:
                return json.dumps({
                    "success": False,
                    "error": "Sovereign vector database (Qdrant) is currently unavailable or initializing.",
                    "results": []
                })

            results = await rag_retriever.retrieve(query=query, top_k=top_k)

            formatted = []
            for r in results:
                formatted.append({
                    "score": round(r.get("score", 0.0), 4),
                    "text": r.get("text", "").strip(),
                    "source": r.get("metadata", {}).get("source", "unknown")
                })

            return json.dumps({
                "success": True,
                "query": query,
                "total_found": len(formatted),
                "results": formatted
            })
        except Exception as e:
            logger.error(f"KnowledgeSearchTool error: {e}")
            return json.dumps({"success": False, "error": str(e), "results": []})


class IndexDocumentTool(BaseTool):
    name = "index_document"
    description = "Index text or notes into the sovereign vector database so it can be retrieved later using semantic search."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the document"},
            "content": {"type": "string", "description": "Text content of the document"}
        },
        "required": ["title", "content"]
    }

    async def arun(self, title: str, content: str, **kwargs) -> str:
        try:
            vector = await embeddings_service.get_embedding(content)
            if not vector:
                return json.dumps({"success": False, "error": "Failed to generate embedding from local model"})

            await qdrant_client.create_collection()
            point_id = abs(hash(f"{title}_{content[:50]}")) % (10**9)

            success = await qdrant_client.upsert_points([{
                "id": point_id,
                "vector": vector,
                "payload": {
                    "title": title,
                    "text": content,
                    "source": title
                }
            }])

            return json.dumps({
                "success": success,
                "title": title,
                "point_id": point_id,
                "message": f"Document '{title}' successfully indexed into sovereign vector store."
            })
        except Exception as e:
            logger.error(f"IndexDocumentTool error: {e}")
            return json.dumps({"success": False, "error": str(e)})


@tool
async def search_knowledge_base(query: str, top_k: int = 4) -> str:
    """
    Search indexed sovereign technical documentation, manuals, incident reports, and regulations
    using semantic vector search. Returns the most relevant excerpts with similarity scores.
    """
    t = KnowledgeSearchTool()
    return await t.arun(query=query, top_k=top_k)


@tool
async def index_document(title: str, content: str) -> str:
    """
    Index text or notes into the sovereign vector database so it can be retrieved later using semantic search.
    """
    t = IndexDocumentTool()
    return await t.arun(title=title, content=content)
