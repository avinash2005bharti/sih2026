"""
Centralized Valkey/Redis Cache Service for Sovereign AI Workbench.
SIH 26117

Key design: sih26117:v1:{scope}:{agent}:{sha256(content)}
TTL strategy:
  - Route cache:   300s
  - RAG cache:     600s
  - Embedding:     3600s
  - Document meta: 600s
  - Session:       3600s

Graceful degraded mode: if Valkey is unavailable, all operations
are no-ops and the system continues without cache.
"""

import json
import hashlib
import time
import os
from typing import Any, Optional, Callable, Awaitable
from core.logging import logger


# ============================================================
# CACHE KEY HELPERS
# ============================================================

PROJECT_PREFIX = "sih26117:v1"


def make_key(*parts: str) -> str:
    """Build a namespaced cache key from parts."""
    return ":".join([PROJECT_PREFIX] + [str(p) for p in parts])


def hash_text(text: str) -> str:
    """SHA-256 hash of text, truncated to 16 hex chars for readability."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def route_key(query: str) -> str:
    """Cache key for model routing decisions."""
    return make_key("route", hash_text(query.strip().lower()))


def rag_key(agent: str, query: str) -> str:
    """Cache key for RAG retrieval results."""
    return make_key("rag", agent, hash_text(query.strip().lower()))


def embedding_key(text: str) -> str:
    """Cache key for embedding vectors."""
    return make_key("embed", hash_text(text.strip()))


def document_key(document_id: str) -> str:
    """Cache key for document metadata."""
    return make_key("doc", document_id)


def session_key(session_id: str) -> str:
    """Cache key for session context."""
    return make_key("session", session_id)


def tool_key(tool_name: str, args_hash: str) -> str:
    """Cache key for deterministic tool results."""
    return make_key("tool", tool_name, args_hash)


# ============================================================
# TTL CONSTANTS (seconds)
# ============================================================

TTL_ROUTE = 300       # 5 min — routing decisions
TTL_RAG = 600         # 10 min — RAG retrieval results
TTL_EMBEDDING = 3600  # 1 hour — embedding vectors
TTL_DOCUMENT = 600    # 10 min — document metadata
TTL_SESSION = 3600    # 1 hour — session state
TTL_TOOL = 300        # 5 min — deterministic tool results
TTL_SHORT = 60        # 1 min — temporary / volatile


# ============================================================
# CACHE SERVICE
# ============================================================

class CacheService:
    """
    Async Valkey/Redis cache client for Sovereign AI Workbench.

    Uses redis.asyncio which is protocol-compatible with Valkey.
    Operates in graceful degraded mode if Valkey is unavailable.
    """

    def __init__(self):
        self._client = None
        self._enabled = False
        self._connected = False

        # Stats counters
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._errors = 0
        self._evictions = 0

        self._connect_start = time.time()

    async def connect(self) -> bool:
        """Initialize connection to Valkey. Returns True if successful."""
        try:
            import redis.asyncio as aioredis

            url = os.environ.get("VALKEY_URL", "redis://localhost:6379")
            logger.info(f"[CACHE] Connecting to Valkey at: {url}")

            self._client = aioredis.from_url(
                url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=3.0,
                socket_timeout=3.0,
                retry_on_timeout=False,
                health_check_interval=30,
            )

            # Verify connection with PING
            t_start = time.monotonic()
            pong = await self._client.ping()
            latency_ms = round((time.monotonic() - t_start) * 1000, 2)

            if pong:
                self._connected = True
                self._enabled = True
                logger.info(f"[CACHE] ✅ Valkey connected — latency={latency_ms}ms, url={url}")
                return True
            else:
                logger.warning("[CACHE] Valkey PING failed — operating in degraded mode")
                return False

        except ImportError:
            logger.warning("[CACHE] redis package not installed — `pip install redis>=5.0.0` — degraded mode")
            return False
        except Exception as e:
            logger.warning(f"[CACHE] Valkey connection failed: {e} — degraded mode (cache disabled)")
            self._connected = False
            self._enabled = False
            return False

    async def close(self):
        """Close the Valkey connection."""
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None
            self._connected = False

    @property
    def is_available(self) -> bool:
        return self._enabled and self._connected and self._client is not None

    # ------------------------------------------------------------------
    # CORE OPERATIONS
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value. Returns None on miss or error."""
        if not self.is_available:
            return None
        try:
            raw = await self._client.get(key)
            if raw is None:
                self._misses += 1
                return None
            self._hits += 1
            return json.loads(raw)
        except Exception as e:
            self._errors += 1
            logger.debug(f"[CACHE] GET error for key={key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = TTL_ROUTE) -> bool:
        """Set a cached value with TTL in seconds."""
        if not self.is_available:
            return False
        try:
            serialized = json.dumps(value, default=str)
            await self._client.setex(key, ttl, serialized)
            self._sets += 1
            return True
        except Exception as e:
            self._errors += 1
            logger.debug(f"[CACHE] SET error for key={key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cached key."""
        if not self.is_available:
            return False
        try:
            await self._client.delete(key)
            self._evictions += 1
            return True
        except Exception as e:
            self._errors += 1
            logger.debug(f"[CACHE] DELETE error for key={key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        if not self.is_available:
            return False
        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            self._errors += 1
            return False

    async def ttl(self, key: str) -> int:
        """Return TTL in seconds. -1 = no expiry, -2 = not found."""
        if not self.is_available:
            return -2
        try:
            return await self._client.ttl(key)
        except Exception:
            return -2

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl: int = TTL_ROUTE,
    ) -> Any:
        """
        Get from cache or call factory, cache the result, and return it.
        Logs CACHE HIT or CACHE MISS.
        """
        cached = await self.get(key)
        if cached is not None:
            logger.info(f"[CACHE] HIT  key={key}")
            return cached, True  # (value, cache_hit)

        logger.info(f"[CACHE] MISS key={key}")
        result = await factory()
        if result is not None:
            await self.set(key, result, ttl=ttl)
            logger.info(f"[CACHE] SET  key={key} ttl={ttl}s")
        return result, False  # (value, cache_hit)

    async def ping(self) -> float:
        """Ping Valkey and return round-trip latency in ms. Returns -1 if unavailable."""
        if not self.is_available:
            return -1.0
        try:
            t = time.monotonic()
            await self._client.ping()
            return round((time.monotonic() - t) * 1000, 2)
        except Exception:
            return -1.0

    # ------------------------------------------------------------------
    # STATS & HEALTH
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return cache statistics dict."""
        total = self._hits + self._misses
        hit_rate = round(self._hits / total * 100, 1) if total > 0 else 0.0
        return {
            "connected": self._connected,
            "enabled": self._enabled,
            "hits": self._hits,
            "misses": self._misses,
            "sets": self._sets,
            "errors": self._errors,
            "evictions": self._evictions,
            "hit_rate_pct": hit_rate,
            "total_requests": total,
        }

    async def health(self) -> dict:
        """Return health status with live latency."""
        latency = await self.ping()
        stats = self.get_stats()
        return {
            "status": "ok" if self._connected else "unavailable",
            "connected": self._connected,
            "latency_ms": latency,
            **stats,
        }


# Global singleton
cache_service = CacheService()
