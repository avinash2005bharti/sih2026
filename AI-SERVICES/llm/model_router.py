"""
Intelligent model routing and task classification for Sovereign AI Workbench.
Classifies tasks into {general_chat, code_task, vision/multimodal_task, file_operation, retrieval/memory_lookup, mixed/multi-step}
and routes requests to the optimal local Ollama model.
"""

from typing import Dict, Any, Optional, Tuple
from core.config import settings
from core.logging import logger


class ModelRouter:
    """Routes tasks to appropriate models based on capabilities and content analysis."""

    def __init__(self):
        """Initialize router with model configuration."""
        self.models = {
            "chat": settings.OLLAMA_CHAT_MODEL,
            "coding": settings.OLLAMA_CODE_MODEL,
            "vision": settings.OLLAMA_VISION_MODEL,
            "embedding": settings.OLLAMA_EMBED_MODEL,
            "general_chat": settings.OLLAMA_CHAT_MODEL,
            "code_task": settings.OLLAMA_CODE_MODEL,
            "vision/multimodal_task": settings.OLLAMA_VISION_MODEL,
            "file_operation": settings.OLLAMA_CODE_MODEL,
            "retrieval/memory_lookup": settings.OLLAMA_CHAT_MODEL,
            "mixed/multi-step": settings.OLLAMA_CHAT_MODEL,
        }

        # Keywords for fast, rule-based classification
        self.coding_keywords = [
            "code", "python", "javascript", "java", "c++", "cpp", "c#", "rust", "go",
            "function", "algorithm", "debug", "error", "exception", "syntax", "compile",
            "refactor", "unit test", "assert", "class", "module", "script", "program",
            "sql", "query", "html", "css", "react", "vue", "calculate", "sum", "add"
        ]

        self.vision_keywords = [
            "image", "photo", "picture", "visual", "diagram", "screenshot", "chart",
            "graph", "plot", "figure", "illustrate", "ocr", "extract from image"
        ]

        self.file_keywords = [
            "file", "directory", "folder", "write to", "save to", "read file",
            "create file", "delete file", "list files", "mkdir", "csv", "spreadsheet", "pdf"
        ]

        self.retrieval_keywords = [
            "search", "lookup", "documentation", "manual", "find in docs",
            "knowledge base", "remember", "recall", "past conversation", "history"
        ]

    def classify_task(self, message: str) -> Dict[str, Any]:
        """
        Classify incoming user message into a discrete task type.
        Returns dict with task_type, recommended_model, and confidence.
        """
        msg_lower = message.lower()

        # Check multi-step indicators (e.g. "and then", "first ... then", multiple instructions)
        is_multi_step = any(phrase in msg_lower for phrase in ["then", "and run", "and execute", "after that", "first"])
        has_file = any(kw in msg_lower for kw in self.file_keywords)
        has_code = any(kw in msg_lower for kw in self.coding_keywords)

        if is_multi_step and (has_file or has_code):
            return {
                "task_type": "mixed/multi-step",
                "recommended_model": self.models["coding"],
                "confidence": 0.90,
                "reason": "Multi-step plan with code or file operations detected"
            }

        if any(kw in msg_lower for kw in self.vision_keywords):
            return {
                "task_type": "vision/multimodal_task",
                "recommended_model": self.models["vision"],
                "confidence": 0.95,
                "reason": "Visual/image analysis keywords detected"
            }

        if has_code:
            return {
                "task_type": "code_task",
                "recommended_model": self.models["coding"],
                "confidence": 0.95,
                "reason": "Code generation or programming keywords detected"
            }

        if has_file:
            return {
                "task_type": "file_operation",
                "recommended_model": self.models["coding"],
                "confidence": 0.90,
                "reason": "File system manipulation keywords detected"
            }

        if any(kw in msg_lower for kw in self.retrieval_keywords):
            return {
                "task_type": "retrieval/memory_lookup",
                "recommended_model": self.models["chat"],
                "confidence": 0.85,
                "reason": "Retrieval or memory query keywords detected"
            }

        return {
            "task_type": "general_chat",
            "recommended_model": self.models["chat"],
            "confidence": 0.80,
            "reason": "General conversational query"
        }

    def route(self, message: str, task_type: str = "auto", preferred_model: str = None) -> str:
        """Route message to the optimal local model."""
        if preferred_model and preferred_model in self.models.values():
            return preferred_model

        if task_type == "auto" or task_type not in self.models:
            classification = self.classify_task(message)
            model = classification["recommended_model"]
            logger.info(f"[ROUTER] Classified task '{classification['task_type']}' (conf={classification['confidence']}) → model={model}")
            return model

        model = self.models.get(task_type, self.models["chat"])
        logger.info(f"[ROUTER] Explicit task_type='{task_type}' → model={model}")
        return model

    def get_all_models(self) -> Dict[str, str]:
        """Return all available model mappings."""
        return dict(self.models)

    def get_roles(self) -> Dict[str, str]:
        """Return primary role-based model configurations."""
        return {
            "chat": self.models.get("chat", settings.OLLAMA_CHAT_MODEL),
            "coding": self.models.get("coding", settings.OLLAMA_CODE_MODEL),
            "vision": self.models.get("vision", settings.OLLAMA_VISION_MODEL),
            "embedding": self.models.get("embedding", settings.OLLAMA_EMBED_MODEL)
        }

    def set_role(self, role: str, model_name: str):
        """Update active model assignment for a given role."""
        if role in ["chat", "coding", "vision", "embedding"]:
            self.models[role] = model_name
            if role == "chat":
                self.models["general_chat"] = model_name
                self.models["retrieval/memory_lookup"] = model_name
                self.models["mixed/multi-step"] = model_name
            elif role == "coding":
                self.models["code_task"] = model_name
                self.models["file_operation"] = model_name
            elif role == "vision":
                self.models["vision/multimodal_task"] = model_name
            logger.info(f"[ROUTER] Configured role '{role}' -> '{model_name}'")


# Global singleton router
model_router = ModelRouter()
