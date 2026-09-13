"""
Embeddings service using Ollama embeddings model.
Generates text embeddings for RAG pipeline.
"""

from typing import List
from llm.ollama_client import ollama_client
from core.config import settings
from core.logging import logger


class EmbeddingsService:
    """Generate text embeddings using Ollama."""

    def __init__(self, model: str = None):
        """Initialize embeddings service."""
        self.model = model or settings.OLLAMA_EMBED_MODEL
        logger.info(f"Initialized embeddings service with model: {self.model}")

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to embed_text")
            return []

        try:
            embedding = await ollama_client.generate_embedding(self.model, text)
            logger.debug(f"Generated embedding for text (len={len(text)})")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """Alias for embed_text."""
        return await self.embed_text(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            try:
                embedding = await self.embed_text(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed text: {e}")
                embeddings.append([])  # Return empty embedding on failure

        return embeddings

    async def similarity_search(self, query_text: str, embeddings: List[List[float]], texts: List[str], k: int = 5) -> List[tuple]:
        """
        Find most similar texts using cosine similarity.

        Args:
            query_text: Query text to find similar texts for
            embeddings: Pre-computed embeddings for candidate texts
            texts: Original texts corresponding to embeddings
            k: Number of results to return

        Returns:
            List of (text, similarity_score) tuples, sorted by similarity
        """
        try:
            query_embedding = await self.embed_text(query_text)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []

        if not query_embedding:
            logger.warning("Query embedding is empty")
            return []

        # Calculate cosine similarity
        scores = []
        for i, embedding in enumerate(embeddings):
            if not embedding:
                scores.append((i, 0.0))
                continue

            similarity = self._cosine_similarity(query_embedding, embedding)
            scores.append((i, similarity))

        # Sort by similarity score and return top k
        scores.sort(key=lambda x: x[1], reverse=True)
        results = [(texts[idx], score) for idx, score in scores[:k]]

        logger.debug(f"Similarity search found {len(results)} results for query")
        return results

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


# Global embeddings service instance
embeddings_service = EmbeddingsService()
