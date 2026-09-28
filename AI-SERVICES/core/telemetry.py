"""
Structured Latency Telemetry for Sovereign AI Workbench.
SIH 26117

Every request logs a structured JSON summary with timing breakdown:
  request_id, agent, selected_model,
  routing_ms, planning_ms, rag_ms, tool_ms, llm_ms, total_ms,
  cache_hit, cache_key, tokens_in, tokens_out
"""

import time
import uuid
import json
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Optional
from core.logging import logger


@dataclass
class RequestTelemetry:
    """Tracks timing and cache stats for a single chat request."""

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    agent: str = "general"
    selected_model: str = "unknown"

    # Timing (ms)
    routing_ms: float = 0.0
    planning_ms: float = 0.0
    rag_ms: float = 0.0
    tool_ms: float = 0.0
    llm_ms: float = 0.0
    total_ms: float = 0.0

    # Cache info
    cache_hit: bool = False
    cache_key: Optional[str] = None

    # Tokens (if available from Ollama response)
    tokens_in: int = 0
    tokens_out: int = 0

    # Internal start time
    _start: float = field(default_factory=time.monotonic, repr=False)

    def start(self):
        """Reset start time."""
        self._start = time.monotonic()

    def finalize(self):
        """Compute total_ms from start."""
        self.total_ms = round((time.monotonic() - self._start) * 1000, 1)

    def log_summary(self):
        """Emit a structured JSON log line with all timing info."""
        self.finalize()
        summary = {
            "request_id": self.request_id,
            "agent": self.agent,
            "model": self.selected_model,
            "routing_ms": round(self.routing_ms, 1),
            "planning_ms": round(self.planning_ms, 1),
            "rag_ms": round(self.rag_ms, 1),
            "tool_ms": round(self.tool_ms, 1),
            "llm_ms": round(self.llm_ms, 1),
            "total_ms": round(self.total_ms, 1),
            "cache_hit": self.cache_hit,
            "cache_key": self.cache_key,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
        }
        logger.info(f"[TELEMETRY] {json.dumps(summary)}")
        return summary

    def to_dict(self) -> dict:
        """Return telemetry as a dict for embedding in API responses."""
        self.finalize()
        return {
            "request_id": self.request_id,
            "agent": self.agent,
            "selected_model": self.selected_model,
            "routing_ms": round(self.routing_ms, 1),
            "planning_ms": round(self.planning_ms, 1),
            "rag_ms": round(self.rag_ms, 1),
            "tool_ms": round(self.tool_ms, 1),
            "llm_ms": round(self.llm_ms, 1),
            "total_ms": round(self.total_ms, 1),
            "cache_hit": self.cache_hit,
            "cache_key": self.cache_key,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
        }


@contextmanager
def timer(telemetry: RequestTelemetry, field_name: str):
    """
    Synchronous context manager that measures elapsed time and
    stores it into a field on the telemetry object.

    Usage:
        with timer(tel, "routing_ms"):
            result = model_router.classify(...)
    """
    t0 = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = (time.monotonic() - t0) * 1000
        current = getattr(telemetry, field_name, 0.0)
        setattr(telemetry, field_name, round(current + elapsed_ms, 1))


@asynccontextmanager
async def async_timer(telemetry: RequestTelemetry, field_name: str):
    """
    Async context manager that measures elapsed time and
    stores it into a field on the telemetry object.

    Usage:
        async with async_timer(tel, "llm_ms"):
            reply = await ollama_client.chat(...)
    """
    t0 = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = (time.monotonic() - t0) * 1000
        current = getattr(telemetry, field_name, 0.0)
        setattr(telemetry, field_name, round(current + elapsed_ms, 1))
