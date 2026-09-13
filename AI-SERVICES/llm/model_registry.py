from typing import Optional
from core.config import settings
from core.logging import logger

class ModelRegistry:
    def __init__(self):
        self._registry = {
            "chat": settings.OLLAMA_CHAT_MODEL,
            "coding": settings.OLLAMA_CODE_MODEL,
            "vision": settings.OLLAMA_VISION_MODEL,
            "embedding": settings.OLLAMA_EMBED_MODEL,
            "reasoning": settings.OLLAMA_CHAT_MODEL,  # reuse chat model for now
        }

    def get_model(self, task_type: str = "chat") -> str:
        model = self._registry.get(task_type)
        if not model:
            logger.warning(f"No model for task_type='{task_type}', falling back to chat")
            model = self._registry["chat"]
        return model

    def supports_tools(self, model_name: str) -> bool:
        """Check whether a given model reliably supports tool calling."""
        name_lower = (model_name or "").lower()
        tool_capable_patterns = ["qwen2.5", "llama3.1", "llama3.2", "mistral", "hermes", "command-r", "firefunction"]
        return any(pat in name_lower for pat in tool_capable_patterns)

    def get_agent_model(self, requested_model: Optional[str] = None) -> str:
        """
        Return a verified tool-capable model for Agent mode.
        If requested_model supports tools, return it. Otherwise fall back to OLLAMA_CODE_MODEL.
        """
        if requested_model and requested_model != "auto" and self.supports_tools(requested_model):
            return requested_model
        return self._registry["coding"]  # default verified tool-capable model (qwen2.5-coder:3b)

    def list_models(self) -> dict:
        return dict(self._registry)

model_registry = ModelRegistry()