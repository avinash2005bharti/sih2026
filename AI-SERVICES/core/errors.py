"""
Error Taxonomy for Sovereign On-Premise AI Workbench (SIH 26117).
Provides structured error codes and exception classes for predictable diagnostics.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(str, Enum):
    """Canonical error codes for AI Services."""
    ROUTING_ERROR = "ROUTING_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    OLLAMA_ERROR = "OLLAMA_ERROR"
    VISION_INPUT_ERROR = "VISION_INPUT_ERROR"
    OCR_ERROR = "OCR_ERROR"
    DOCUMENT_EXTRACTION_ERROR = "DOCUMENT_EXTRACTION_ERROR"
    EMBEDDING_ERROR = "EMBEDDING_ERROR"
    QDRANT_ERROR = "QDRANT_ERROR"
    RAG_EMPTY_RESULT = "RAG_EMPTY_RESULT"
    RAG_LOW_RELEVANCE = "RAG_LOW_RELEVANCE"
    DATABASE_ERROR = "DATABASE_ERROR"
    FILE_GENERATION_ERROR = "FILE_GENERATION_ERROR"
    FILE_VALIDATION_ERROR = "FILE_VALIDATION_ERROR"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    AGENT_MAX_STEPS = "AGENT_MAX_STEPS"


class SovereignAIError(Exception):
    """Base exception for all Sovereign AI workbench errors."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        super().__init__(message)
        self.code = code.value if isinstance(code, ErrorCode) else str(code)
        self.message = message
        self.details = details or {}
        self.retryable = retryable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable
        }
