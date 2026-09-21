"""
Qdrant Vector Database Client for Sovereign AI Workbench.
Handles storage, dimension validation, verified upserts, and semantic retrieval of document embeddings.
"""

import httpx
from typing import List, Dict, Optional, Any
from core.config import settings
from core.logging import logger


class QdrantClient:
    """Client for Qdrant vector database operations with strict verification and dimension validation."""

    def __init__(self, url: str = None, collection: str = None, vector_size: int = None):
        raw_url = url or getattr(settings, "QDRANT_URL", "http://localhost:6333")
        self.url = raw_url.rstrip("/")
        self.collection = collection or getattr(settings, "QDRANT_COLLECTION", "sovereign_documents")
        self.vector_size = vector_size or getattr(settings, "QDRANT_VECTOR_SIZE", 768)
        self._initialized = False
        logger.info(f"[QDRANT] Initialized Qdrant client | url={self.url} | collection={self.collection} | dim={self.vector_size}")

    def _get_urls(self) -> List[str]:
        """Return candidate URLs for Windows host vs container environments."""
        urls = [self.url]
        if "localhost" in self.url:
            urls.append(self.url.replace("localhost", "127.0.0.1"))
            urls.append(self.url.replace("localhost", "host.docker.internal"))
        elif "127.0.0.1" in self.url:
            urls.append(self.url.replace("127.0.0.1", "localhost"))
        elif "qdrant:6333" in self.url:
            urls.append("http://localhost:6333")
            urls.append("http://127.0.0.1:6333")
        return urls

    async def health_check(self) -> bool:
        """Check if Qdrant service is accessible."""
        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(f"{u}/healthz")
                    if resp.status_code == 200:
                        self.url = u
                        return True
                    resp = await client.get(f"{u}/collections")
                    if resp.status_code in [200, 204]:
                        self.url = u
                        return True
            except Exception as e:
                logger.debug(f"[QDRANT] Health check failed for {u}: {e}")
        return False

    async def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get collection metadata including vector size and points count."""
        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{u}/collections/{self.collection}")
                    if resp.status_code == 200:
                        data = resp.json().get("result", {})
                        return data
            except Exception as e:
                logger.debug(f"[QDRANT] get_collection_info failed for {u}: {e}")
        return None

    async def collection_exists(self) -> bool:
        """Check if target collection exists."""
        info = await self.get_collection_info()
        return info is not None

    async def validate_collection_dimension(self, expected_dim: int) -> bool:
        """
        Validate that the collection vector size matches the expected embedding dimension.
        If there is a mismatch, logs detailed warning and provides recreation guidance.
        """
        info = await self.get_collection_info()
        if not info:
            return False

        config_params = info.get("config", {}).get("params", {})
        existing_size = config_params.get("vectors", {}).get("size")
        if existing_size and existing_size != expected_dim:
            logger.error(
                f"[QDRANT] DIMENSION MISMATCH: Collection '{self.collection}' has dimension {existing_size}, "
                f"but embedding model produces {expected_dim} dimensions! "
                f"Vectors cannot be inserted into a mismatched collection."
            )
            return False
        return True

    async def create_collection(self, vector_size: Optional[int] = None) -> bool:
        """Create or validate Qdrant collection idempotently."""
        dim = vector_size or self.vector_size
        info = await self.get_collection_info()

        if info:
            existing_size = info.get("config", {}).get("params", {}).get("vectors", {}).get("size")
            if existing_size and existing_size != dim:
                logger.warning(
                    f"[QDRANT] Existing collection dimension {existing_size} != target {dim}. "
                    f"Recreating collection '{self.collection}' with dimension {dim}."
                )
                await self.delete_collection()
            else:
                logger.info(f"[QDRANT] collection={self.collection} already exists with dimension={dim}")
                await self._ensure_payload_indexes()
                return True

        payload = {
            "vectors": {
                "size": dim,
                "distance": "Cosine"
            }
        }

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.put(f"{u}/collections/{self.collection}", json=payload)
                    if resp.status_code in [200, 201]:
                        self.url = u
                        logger.info(f"[QDRANT] collection={self.collection} created with dimension={dim}")
                        await self._ensure_payload_indexes()
                        return True
            except Exception as e:
                logger.error(f"[QDRANT] Failed to create collection via {u}: {e}")

        return False

    async def _ensure_payload_indexes(self) -> None:
        """Ensure payload indexes exist for document_id and filename for high-speed filtering."""
        fields = [
            ("document_id", "keyword"),
            ("filename", "keyword"),
            ("source", "keyword"),
            ("chunk_id", "keyword"),
            ("user_id", "keyword"),
        ]
        for field_name, field_type in fields:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.put(
                        f"{self.url}/collections/{self.collection}/index",
                        json={"field_name": field_name, "field_schema": field_type}
                    )
            except Exception:
                pass

    async def get_points_count(self, filter_dict: Optional[Dict] = None, document_id: Optional[str] = None) -> int:
        """Query exact count of points in the collection or matching a filter."""
        payload: Dict[str, Any] = {"exact": True}
        if document_id:
            payload["filter"] = {"must": [{"key": "document_id", "match": {"value": str(document_id)}}]}
        elif filter_dict:
            if "must" in filter_dict or "should" in filter_dict or "must_not" in filter_dict:
                payload["filter"] = filter_dict
            else:
                must_clauses = [{"key": k, "match": {"value": str(v)}} for k, v in filter_dict.items()]
                payload["filter"] = {"must": must_clauses}

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.post(f"{u}/collections/{self.collection}/points/count", json=payload)
                    if resp.status_code == 200:
                        return resp.json().get("result", {}).get("count", 0)
            except Exception as e:
                logger.debug(f"[QDRANT] Points count query error on {u}: {e}")
        return 0

    async def get_sample_point(self, document_id: Optional[str] = None, filter_dict: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a sample point to verify readability and payload integrity."""
        scroll_payload: Dict[str, Any] = {
            "limit": 1,
            "with_payload": True,
            "with_vector": False
        }
        if document_id:
            scroll_payload["filter"] = {
                "must": [{"key": "document_id", "match": {"value": str(document_id)}}]
            }
        elif filter_dict:
            if "must" in filter_dict or "should" in filter_dict or "must_not" in filter_dict:
                scroll_payload["filter"] = filter_dict
            else:
                must_clauses = [{"key": k, "match": {"value": str(v)}} for k, v in filter_dict.items()]
                scroll_payload["filter"] = {"must": must_clauses}

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.post(f"{u}/collections/{self.collection}/points/scroll", json=scroll_payload)
                    if resp.status_code == 200:
                        pts = resp.json().get("result", {}).get("points", [])
                        if pts:
                            return pts[0]
            except Exception as e:
                logger.debug(f"[QDRANT] get_sample_point error on {u}: {e}")
        return None

    async def upsert_points(self, points: List[Dict[str, Any]], wait: bool = True) -> bool:
        """
        Upsert points into collection with wait=true to guarantee synchronous write confirmation.
        """
        if not points:
            logger.warning("[QDRANT] upserting=0 (no points provided)")
            return False

        # Validate first point vector size
        sample_vec = points[0].get("vector", [])
        if not sample_vec or len(sample_vec) != self.vector_size:
            logger.error(
                f"[QDRANT] Vector size mismatch before upsert: vector={len(sample_vec)}, expected={self.vector_size}"
            )
            return False

        existing_count = await self.get_points_count()
        logger.info(f"[QDRANT] collection={self.collection} existing_points={existing_count} upserting={len(points)}")

        payload = {"points": points}
        url_param = "?wait=true" if wait else ""

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.put(f"{u}/collections/{self.collection}/points{url_param}", json=payload)
                    if resp.status_code in [200, 201]:
                        self.url = u
                        logger.info(f"[QDRANT] upsert_success=true (status={resp.status_code})")
                        return True
                    else:
                        logger.error(f"[QDRANT] Upsert error ({resp.status_code}): {resp.text}")
            except Exception as e:
                logger.error(f"[QDRANT] Failed to upsert points on {u}: {e}")

        return False

    async def verify_ingestion(self, document_id: str, expected_min_chunks: int = 1, expected_points: Optional[int] = None) -> Dict[str, Any]:
        """
        Explicit post-upsert verification:
        Checks point count for document_id and retrieves a sample point.
        """
        target_min = expected_points if expected_points is not None else expected_min_chunks
        filter_dict = {
            "must": [{"key": "document_id", "match": {"value": str(document_id)}}]
        }
        points_count = await self.get_points_count(filter_dict=filter_dict)
        sample_pt = await self.get_sample_point(document_id=document_id)
        sample_found = sample_pt is not None

        logger.info(
            f"[VERIFY] document_id={document_id} points_count={points_count} sample_point_found={sample_found}"
        )

        success = (points_count >= target_min) and sample_found
        return {
            "verified": success,
            "document_id": document_id,
            "points_count": points_count,
            "sample_point_found": sample_found,
            "sample_point_id": sample_pt.get("id") if sample_pt else None
        }


    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.0,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search similar vectors in Qdrant."""
        payload = {
            "vector": query_vector,
            "limit": limit,
            "score_threshold": score_threshold,
            "with_payload": True
        }
        if filter_dict:
            payload["filter"] = filter_dict

        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(f"{u}/collections/{self.collection}/points/search", json=payload)
                    if resp.status_code == 200:
                        results = resp.json().get("result", [])
                        logger.debug(f"[RAG] Search returned {len(results)} hits from {self.collection}")
                        return results
            except Exception as e:
                logger.error(f"[QDRANT] Search failed on {u}: {e}")
        return []

    async def delete_points_by_document_id(self, document_id: str) -> bool:
        """Delete all vectors for a specific document_id."""
        if not document_id:
            return False
        payload = {
            "filter": {
                "must": [{"key": "document_id", "match": {"value": str(document_id)}}]
            }
        }
        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(f"{u}/collections/{self.collection}/points/delete?wait=true", json=payload)
                    if resp.status_code in [200, 201]:
                        logger.info(f"[QDRANT] Deleted points for document_id={document_id}")
                        return True
            except Exception as e:
                logger.error(f"[QDRANT] Delete points error on {u}: {e}")
        return False

    async def delete_points_by_filename(self, filename: str) -> bool:
        """Delete all vectors for a specific filename or source."""
        if not filename:
            return False
        payload = {
            "filter": {
                "should": [
                    {"key": "filename", "match": {"value": str(filename)}},
                    {"key": "source", "match": {"value": str(filename)}}
                ]
            }
        }
        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(f"{u}/collections/{self.collection}/points/delete?wait=true", json=payload)
                    if resp.status_code in [200, 201]:
                        logger.info(f"[QDRANT] Deleted points for filename={filename}")
                        return True
            except Exception as e:
                logger.error(f"[QDRANT] Delete points by filename error on {u}: {e}")
        return False

    async def delete_points_by_source(self, source: str) -> bool:
        return await self.delete_points_by_filename(source)

    async def delete_collection(self) -> bool:
        """Delete collection."""
        for u in self._get_urls():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.delete(f"{u}/collections/{self.collection}")
                    if resp.status_code in [200, 204]:
                        logger.info(f"[QDRANT] Deleted collection '{self.collection}'")
                        return True
            except Exception as e:
                logger.error(f"[QDRANT] Delete collection error on {u}: {e}")
        return False


# Global singleton instance
qdrant_client = QdrantClient()
