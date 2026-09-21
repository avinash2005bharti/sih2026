"""
Embeddings Service using Local Ollama nomic-embed-text for Sovereign RAG pipeline.
Performs dynamic dimension detection, reachability verification, and validated vector generation.
"""

import os
from typing import List, Optional, Tuple
import httpx

from core.config import settings
from core.logging import logger
from llm.model_registry import model_registry


class EmbeddingsService:
    """Generate text embeddings using Ollama nomic-embed-text."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
        if ":" in self.model and not self.model.endswith(":latest"):
            pass
        elif self.model.endswith(":latest"):
            self.model = self.model.replace(":latest", "")

        raw_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = raw_url.rstrip("/")
        self._detected_dimension: Optional[int] = None
        self._last_offline_time: float = 0
        logger.info(f"[EMBED] Initialized embeddings service with model: {self.model} on {self.base_url}")

    def _get_urls(self) -> List[str]:
        """Return candidate URLs for Ollama."""
        urls = [self.base_url]
        if "localhost" in self.base_url:
            urls.append(self.base_url.replace("localhost", "127.0.0.1"))
        elif "127.0.0.1" in self.base_url:
            urls.append(self.base_url.replace("127.0.0.1", "localhost"))
        return urls

    async def detect_dimension(self) -> int:
        """Probe Ollama to detect exact embedding vector dimension (e.g. 768)."""
        if self._detected_dimension and self._detected_dimension > 0:
            return self._detected_dimension

        import time
        if time.time() - self._last_offline_time < 15.0:
            return getattr(settings, "QDRANT_VECTOR_SIZE", 768)

        sample = "benchmark probe"
        test_models = [self.model, "nomic-embed-text"]

        for u in self._get_urls():
            for m in test_models:
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        resp = await client.post(
                            f"{u}/api/embeddings",
                            json={"model": m, "prompt": sample}
                        )
                        if resp.status_code == 200:
                            emb = resp.json().get("embedding", [])
                            if emb:
                                self._detected_dimension = len(emb)
                                self.model = m
                                logger.info(f"[EMBED] Detected dimension: {self._detected_dimension} for model={m}")
                                return self._detected_dimension
                except Exception as e:
                    logger.debug(f"[EMBED] Dimension probe error via {u} with {m}: {e}")

        self._last_offline_time = time.time()
        # Fallback to configured settings
        self._detected_dimension = getattr(settings, "QDRANT_VECTOR_SIZE", 768)
        return self._detected_dimension

    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        Returns vector or None if Ollama is unreachable.
        """
        if not text or not text.strip():
            return None

        import time
        if time.time() - self._last_offline_time < 15.0:
            return None

        clean_text = text.strip()
        test_models = [self.model, "nomic-embed-text"]

        for u in self._get_urls():
            for m in test_models:
                try:
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        resp = await client.post(
                            f"{u}/api/embeddings",
                            json={"model": m, "prompt": clean_text}
                        )
                        if resp.status_code == 200:
                            emb = resp.json().get("embedding", [])
                            if emb:
                                if not self._detected_dimension:
                                    self._detected_dimension = len(emb)
                                return emb
                except Exception as e:
                    logger.debug(f"[EMBED] embed_text attempt via {u} with {m} failed: {e}")

        self._last_offline_time = time.time()
        logger.warning(f"[EMBED] Ollama embeddings unreachable on {self.base_url}, fallback enabled")
        return None

    async def get_embedding(self, text: str) -> List[float]:
        """Alias for embed_text."""
        return await self.embed_text(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Batch generate embeddings for multiple texts using Ollama's /api/embed endpoint.
        Validates every embedding vector before returning.
        Falls back to per-chunk generation if /api/embed is unavailable.
        """
        if not texts:
            return []

        dim = await self.detect_dimension()
        test_models = [self.model, f"{self.model}:latest", "nomic-embed-text", "nomic-embed-text:latest"]

        # 1. Try modern fast batch endpoint /api/embed (batches of 32 chunks)
        batch_size = 32
        all_embeddings: List[List[float]] = []
        batch_success = True

        for batch_start in range(0, len(texts), batch_size):
            batch_slice = texts[batch_start : batch_start + batch_size]
            batch_done = False

            for u in self._get_urls():
                if batch_done:
                    break
                for m in test_models:
                    try:
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            resp = await client.post(
                                f"{u}/api/embed",
                                json={"model": m, "input": batch_slice}
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                batch_embs = data.get("embeddings", [])
                                if len(batch_embs) == len(batch_slice):
                                    all_embeddings.extend(batch_embs)
                                    batch_done = True
                                    break
                    except Exception as e:
                        logger.debug(f"[EMBED] Batch /api/embed attempt via {u} failed: {e}")

            if not batch_done:
                batch_success = False
                break

        if batch_success and len(all_embeddings) == len(texts):
            # Validate dimensions
            for idx, emb in enumerate(all_embeddings):
                if not emb or len(emb) != dim:
                    raise RuntimeError(
                        f"Embedding generation failure on chunk {idx}: expected dimension {dim}, got {len(emb) if emb else 0}"
                    )
            logger.info(f"[EMBED] Fast batch generated={len(all_embeddings)} dimension={dim}")
            return all_embeddings

        # 2. Fallback to per-chunk generation if batch endpoint wasn't accepted
        logger.info("[EMBED] Falling back to sequential embedding generation")
        embeddings: List[List[float]] = []
        for idx, t in enumerate(texts):
            emb = await self.embed_text(t)
            if not emb or len(emb) != dim:
                raise RuntimeError(
                    f"Embedding generation failure on chunk {idx}: expected dimension {dim}, got {len(emb) if emb else 0}"
                )
            embeddings.append(emb)

        logger.info(f"[EMBED] generated={len(embeddings)} dimension={dim}")
        return embeddings

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    async def similarity_search(
        self,
        query_text: str,
        embeddings: List[List[float]],
        texts: List[str],
        k: int = 5
    ) -> List[Tuple[str, float]]:
        """Cosine similarity ranking across precomputed embeddings."""
        query_emb = await self.embed_text(query_text)
        scores = []
        for i, emb in enumerate(embeddings):
            sim = self._cosine_similarity(query_emb, emb)
            scores.append((texts[i], sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


# Global singleton instance
embeddings_service = EmbeddingsService()
