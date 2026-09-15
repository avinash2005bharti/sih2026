"""
LTM Memory Retriever for Sovereign AI Workbench.
Retrieves relevant memories from Qdrant vector store and related entities from Neo4j,
deduplicating and formatting them into a bounded prompt context block.
"""

import os
from typing import Any, Dict, List, Optional
from core.config import settings
from core.logging import logger
from memory.embeddings.embedding_service import embedding_service
from memory.vector.qdrant_service import qdrant_service
from memory.graph.neo4j_service import neo4j_service
from memory.mem0.mem0_service import mem0_service


class MemoryRetriever:
    """Coordinates semantic retrieval from Qdrant, Mem0, and Neo4j."""

    def __init__(
        self,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        max_context: Optional[int] = None
    ):
        self.top_k = int(
            top_k
            or os.getenv("LTM_TOP_K")
            or getattr(settings, "LTM_TOP_K", 5)
        )
        self.score_threshold = float(
            score_threshold
            or os.getenv("LTM_SCORE_THRESHOLD")
            or getattr(settings, "LTM_SCORE_THRESHOLD", 0.35)
        )
        self.max_context = int(
            max_context
            or os.getenv("LTM_MAX_CONTEXT")
            or getattr(settings, "LTM_MAX_CONTEXT", 4000)
        )

    async def retrieve_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute semantic search across Qdrant and Mem0 for relevant memories.
        Deduplicates by content.
        """
        if not query or not query.strip():
            return []

        eff_limit = limit or self.top_k
        eff_threshold = score_threshold if score_threshold is not None else self.score_threshold

        results: List[Dict[str, Any]] = []
        seen_texts = set()

        # 1. Search directly in Qdrant via embedding with asymmetric query prefix
        try:
            q_text = query.strip()
            embed_query = f"search_query: {q_text}" if not q_text.startswith("search_query:") else q_text
            query_vector = await embedding_service.embed_text(embed_query)
            if query_vector:
                qdrant_hits = await qdrant_service.search_memories(
                    query_vector=query_vector,
                    user_id=user_id,
                    limit=eff_limit,
                    score_threshold=eff_threshold
                )
                for h in qdrant_hits:
                    content = h.get("content", "").strip()
                    if content and content.lower() not in seen_texts:
                        seen_texts.add(content.lower())
                        results.append(h)
        except Exception as e:
            logger.warning(f"[LTM] Qdrant search note: {e}")

        # 2. Search via Mem0 if more results needed
        if len(results) < eff_limit:
            try:
                mem0_hits = await mem0_service.search_memories(
                    query=query,
                    user_id=user_id,
                    limit=eff_limit
                )
                for m in mem0_hits:
                    mem_text = m.get("memory", "").strip()
                    if mem_text and mem_text.lower() not in seen_texts:
                        seen_texts.add(mem_text.lower())
                        results.append({
                            "memory_id": m.get("id"),
                            "content": mem_text,
                            "score": m.get("score") or 0.70,
                            "source": "mem0"
                        })
            except Exception as e:
                logger.debug(f"[LTM] Mem0 search note: {e}")

        return results[:eff_limit]

    async def retrieve_graph_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve connected graph entities and relationships from Neo4j."""
        try:
            return await neo4j_service.query_related_context(query, user_id=user_id, limit=limit)
        except Exception as e:
            logger.debug(f"[LTM] Graph retrieval note: {e}")
            return []

    async def build_context_block(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Build a formatted context block containing recalled semantic memories
        and knowledge graph relationships for prompt injection.
        """
        sections = []

        # 1. Semantic LTM memories
        memories = await self.retrieve_memories(query, user_id=user_id)
        if memories:
            sec_lines = ["### Recalled Long-Term Facts & Preferences (LTM):"]
            for m in memories:
                score_str = f" [Score: {m['score']}]" if m.get("score") else ""
                sec_lines.append(f"- {m['content']}{score_str}")
            sections.append("\n".join(sec_lines))

        # 2. Neo4j Knowledge Graph facts
        graph_records = await self.retrieve_graph_context(query, user_id=user_id)
        if graph_records:
            g_lines = ["### Knowledge Graph Insights (Neo4j):"]
            for r in graph_records:
                ent = r.get("entity_name")
                rel = r.get("relationship")
                tgt = r.get("related_target")
                if ent and rel and tgt:
                    g_lines.append(f"- ({ent}) -[:{rel}]-> ({tgt})")
                elif ent:
                    g_lines.append(f"- Entity reference: {ent}")
            if len(g_lines) > 1:
                sections.append("\n".join(g_lines))

        full_context = "\n\n".join(sections)
        # Cap length to LTM_MAX_CONTEXT
        if len(full_context) > self.max_context:
            full_context = full_context[:self.max_context] + "...\n[LTM context truncated]"

        return full_context


# Global singleton instance
memory_retriever = MemoryRetriever()
