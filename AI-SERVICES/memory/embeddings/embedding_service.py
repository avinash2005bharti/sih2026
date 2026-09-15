"""
Local Ollama Embedding Service for Sovereign AI Workbench.
Handles dynamic dimension detection, reachability testing, and vector embeddings generation.
"""

import os
import httpx
from typing import List, Optional, Dict, Any
from core.config import settings
from core.logging import logger


class EmbeddingService:
    """Local embedding service powered by local Ollama instance."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        raw_url = base_url or os.getenv("OLLAMA_BASE_URL") or settings.OLLAMA_BASE_URL
        self.base_url = raw_url.rstrip("/")
        # Model name default
        self.model = (
            model
            or os.getenv("OLLAMA_EMBEDDING_MODEL")
            or getattr(settings, "OLLAMA_EMBEDDING_MODEL", None)
            or getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
        )
        if ":" in self.model and not self.model.endswith(":latest"):
            # keep full model tag
            pass
        elif self.model.endswith(":latest"):
            self.model = self.model.replace(":latest", "")

        self._detected_dimension: Optional[int] = None
        logger.info(f"[EMBEDDING] Initialized EmbeddingService (URL: {self.base_url}, Model: {self.model})")

    def _get_urls(self) -> List[str]:
        """Return primary and fallback URLs for host vs container vs IPv4/IPv6 environments."""
        urls = [self.base_url]
        if "localhost" in self.base_url:
            urls.append(self.base_url.replace("localhost", "127.0.0.1"))
            urls.append(self.base_url.replace("localhost", "host.docker.internal"))
        elif "127.0.0.1" in self.base_url:
            urls.append(self.base_url.replace("127.0.0.1", "localhost"))
            urls.append(self.base_url.replace("127.0.0.1", "host.docker.internal"))
        elif "host.docker.internal" in self.base_url:
            urls.append("http://localhost:11434")
            urls.append("http://127.0.0.1:11434")
        return urls

    def _resolve_url(self) -> str:
        """Resolve candidate URLs for host vs container environments."""
        return self._get_urls()[0]

    async def check_health(self) -> dict:
        """
        Probe Ollama reachability and verify embedding model presence and dimension.
        """
        urls = self._get_urls()
        last_error = None
        for u in urls:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(f"{u}/api/tags")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = [m.get("name", "") for m in data.get("models", [])]
                        has_model = any(self.model in m for m in models)
                        
                        dim = await self.detect_dimension(base_url=u)
                        return {
                            "status": "healthy" if has_model and dim > 0 else "degraded",
                            "available": True,
                            "url": u,
                            "model": self.model,
                            "model_present": has_model,
                            "dimension": dim,
                            "available_models": models
                        }
            except Exception as e:
                last_error = str(e)

        return {
            "status": "unavailable",
            "available": False,
            "url": self.base_url,
            "model": self.model,
            "error": last_error or "Connection refused"
        }

    async def detect_dimension(self, base_url: Optional[str] = None) -> int:
        """Dynamically detect and validate vector dimension by testing a sample prompt."""
        if self._detected_dimension and self._detected_dimension > 0:
            return self._detected_dimension

        urls = [base_url] if base_url else self._get_urls()
        candidate_models = [self.model]
        if ":latest" not in self.model:
            candidate_models.append(f"{self.model}:latest")

        for u in urls:
            u_clean = u.rstrip("/")
            for m in candidate_models:
                try:
                    async with httpx.AsyncClient(timeout=8.0) as client:
                        resp = await client.post(
                            f"{u_clean}/api/embeddings",
                            json={"model": m, "prompt": "benchmark probe"}
                        )
                        if resp.status_code == 200:
                            emb = resp.json().get("embedding", [])
                            if emb:
                                self._detected_dimension = len(emb)
                                self.model = m
                                logger.info(f"[EMBEDDING] Detected vector dimension: {self._detected_dimension} for {self.model} via {u_clean}")
                                return self._detected_dimension
                except Exception as e:
                    logger.debug(f"[EMBEDDING] Dimension detection error via {u_clean} with {m}: {e}")

        # Fallback to configured settings or standard 768
        return getattr(settings, "QDRANT_VECTOR_SIZE", 768)

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a given text snippet."""
        if not text or not text.strip():
            return []

        urls = self._get_urls()
        candidate_models = [self.model]
        if ":latest" not in self.model:
            candidate_models.append(f"{self.model}:latest")

        for u in urls:
            u_clean = u.rstrip("/")
            for m in candidate_models:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.post(
                            f"{u_clean}/api/embeddings",
                            json={"model": m, "prompt": text.strip()}
                        )
                        if resp.status_code == 200:
                            emb = resp.json().get("embedding", [])
                            if emb:
                                if not self._detected_dimension:
                                    self._detected_dimension = len(emb)
                                return emb
                except Exception as e:
                    logger.debug(f"[EMBEDDING] Failed via {u_clean} with {m}: {e}")

        logger.error(f"[EMBEDDING] All Ollama embedding endpoints failed for model '{self.model}'")
        return []

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding generation for multiple texts."""
        embeddings = []
        for t in texts:
            emb = await self.embed_text(t)
            embeddings.append(emb)
        return embeddings


# Global singleton instance
embedding_service = EmbeddingService()
