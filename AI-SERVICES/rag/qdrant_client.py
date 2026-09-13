"""
Qdrant vector database client.
Handles storage and retrieval of document embeddings.
"""

import httpx
from typing import List, Dict, Optional
from core.config import settings
from core.logging import logger


class QdrantClient:
    """Client for Qdrant vector database operations."""

    def __init__(self, url: str = None, collection: str = None, vector_size: int = None):
        """
        Initialize Qdrant client.

        Args:
            url: Qdrant API URL
            collection: Collection name
            vector_size: Vector dimension size
        """
        self.url = url or settings.QDRANT_URL
        self.collection = collection or settings.QDRANT_COLLECTION
        self.vector_size = vector_size or settings.QDRANT_VECTOR_SIZE
        logger.info(f"Initialized Qdrant client | url={self.url} | collection={self.collection}")

    async def health_check(self) -> bool:
        """Check if Qdrant is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.url}/health")
                is_healthy = resp.status_code == 200
                if is_healthy:
                    logger.debug("Qdrant health check passed")
                else:
                    logger.warning(f"Qdrant health check failed: {resp.status_code}")
                return is_healthy
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    async def collection_exists(self) -> bool:
        """Check if collection exists."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.url}/collections/{self.collection}")
                return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Collection check failed: {e}")
            return False

    async def create_collection(self) -> bool:
        """Create collection if it doesn't exist."""
        try:
            # Check if exists first
            if await self.collection_exists():
                logger.debug(f"Collection '{self.collection}' already exists")
                return True

            # Create collection
            payload = {
                "vectors": {
                    "size": self.vector_size,
                    "distance": "Cosine"
                }
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.put(
                    f"{self.url}/collections/{self.collection}",
                    json=payload
                )

            if resp.status_code in [200, 201]:
                logger.info(f"Created collection '{self.collection}'")
                return True
            else:
                logger.error(f"Failed to create collection: {resp.status_code} {resp.text}")
                return False

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False

    async def upsert_points(self, points: List[Dict]) -> bool:
        """
        Insert or update points in collection.

        Args:
            points: List of points with id, vector, payload

        Returns:
            Success status
        """
        try:
            payload = {"points": points}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.put(
                    f"{self.url}/collections/{self.collection}/points",
                    json=payload
                )

            if resp.status_code in [200, 201]:
                logger.debug(f"Upserted {len(points)} points")
                return True
            else:
                logger.error(f"Failed to upsert points: {resp.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error upserting points: {e}")
            raise

    async def search(self, query_vector: List[float], limit: int = 5, score_threshold: float = 0.0) -> List[Dict]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            List of search results with scores and payloads
        """
        try:
            payload = {
                "vector": query_vector,
                "limit": limit,
                "score_threshold": score_threshold,
                "with_payload": True
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.url}/collections/{self.collection}/points/search",
                    json=payload
                )

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("result", [])
                logger.debug(f"Search returned {len(results)} results")
                return results
            else:
                logger.error(f"Search failed: {resp.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    async def delete_collection(self) -> bool:
        """Delete the collection."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.delete(f"{self.url}/collections/{self.collection}")

            if resp.status_code == 204:
                logger.info(f"Deleted collection '{self.collection}'")
                return True
            else:
                logger.error(f"Failed to delete collection: {resp.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False

    async def get_collection_info(self) -> Optional[Dict]:
        """Get collection information."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.url}/collections/{self.collection}")

            if resp.status_code == 200:
                return resp.json()
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None


qdrant_client = QdrantClient()
