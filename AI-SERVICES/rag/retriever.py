"""
RAG retriever - combines embeddings and vector database for document search.
"""

from typing import List, Dict, Optional
import uuid
from rag.embeddings import embeddings_service
from rag.qdrant_client import qdrant_client
from core.logging import logger


class RAGRetriever:
    """Retrieves relevant documents using embeddings and vector search."""

    def __init__(self):
        """Initialize RAG retriever."""
        self.embeddings_service = embeddings_service
        self.vector_db = qdrant_client
        logger.info("Initialized RAG retriever")

    async def initialize(self) -> bool:
        """Initialize vector database collection."""
        try:
            # Check Qdrant connectivity
            if not await self.vector_db.health_check():
                logger.error("Qdrant is not accessible")
                return False

            # Create collection if needed
            if not await self.vector_db.create_collection():
                logger.error("Failed to create collection")
                return False

            logger.info("RAG retriever initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing RAG retriever: {e}")
            return False

    async def add_documents(self, documents: List[str], metadata: Optional[List[Dict]] = None) -> bool:
        """
        Add documents to the vector database.

        Args:
            documents: List of document texts to index
            metadata: Optional list of metadata dicts for each document

        Returns:
            Success status
        """
        try:
            logger.info(f"Adding {len(documents)} documents to RAG")

            # Generate embeddings for all documents
            embeddings = await self.embeddings_service.embed_texts(documents)

            # Prepare points for Qdrant
            points = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                if not embedding:
                    logger.warning(f"Skipping document {i} - no embedding generated")
                    continue

                point = {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": {
                        "text": doc,
                        "doc_index": i,
                        "metadata": metadata[i] if metadata else {}
                    }
                }
                points.append(point)

            # Upsert to vector database
            if not points:
                logger.warning("No valid points to upsert")
                return False

            success = await self.vector_db.upsert_points(points)
            if success:
                logger.info(f"Successfully indexed {len(points)} documents")
            return success

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    async def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Dict]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query text
            top_k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            List of relevant documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embeddings_service.embed_text(query)

            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []

            # Search in vector database
            results = await self.vector_db.search(
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.get("score", 0),
                    "text": result.get("payload", {}).get("text", ""),
                    "metadata": result.get("payload", {}).get("metadata", {})
                })

            logger.debug(f"Retrieved {len(formatted_results)} documents for query")
            return formatted_results

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

    async def clear(self) -> bool:
        """Clear all documents from vector database."""
        try:
            logger.info("Clearing all documents from RAG database")
            return await self.vector_db.delete_collection()
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False


# Global retriever instance
rag_retriever = RAGRetriever()
