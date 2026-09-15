from typing import Optional, Dict, Any
from core.config import settings
from core.logging import logger

MODEL_REGISTRY = {
    "general": {
        "provider": "ollama",
        "model": "qwen2.5:1.5b",
        "capabilities": [
            "chat",
            "reasoning",
            "planning",
            "classification",
            "routing"
        ]
    },
    "coding": {
        "provider": "ollama",
        "model": "qwen2.5-coder:1.5b",
        "capabilities": [
            "coding",
            "python",
            "javascript",
            "debugging",
            "automation"
        ]
    },
    "vision": {
        "provider": "ollama",
        "model": "moondream:latest",
        "capabilities": [
            "vision",
            "image_analysis",
            "visual_understanding"
        ]
    },
    "embedding": {
        "provider": "ollama",
        "model": "nomic-embed-text:latest",
        "capabilities": [
            "embedding"
        ]
    }
}

class ModelRegistry:
    def __init__(self):
        self._registry = MODEL_REGISTRY

    def get_model(self, task_type: str = "general") -> str:
        """
        Returns the specific model string for the given task_type mapped in the dictionary.
        Uses 'general' if the task type isn't found.
        """
        if task_type in self._registry:
            return self._registry[task_type]["model"]
        logger.warning(f"No exact match for task_type='{task_type}', falling back to general model")
        return self._registry["general"]["model"]

    def supports_tools(self, model_name: str) -> bool:
        """Check whether a given model reliably supports tool calling."""
        name_lower = (model_name or "").lower()
        # Ensure only the approved tool-capable models return True
        return "qwen2.5-coder" in name_lower or "qwen2.5:1.5b" in name_lower

    def get_agent_model(self, requested_model: Optional[str] = None) -> str:
        """
        Return the requested model. We trust the router or the user to provide a valid model
        for the given task (e.g. moondream for vision, qwen2.5 for general).
        """
        if requested_model and requested_model != "auto":
            return requested_model
        return self._registry["coding"]["model"]

    def get_model_capabilities(self, model_group: str) -> list:
        if model_group in self._registry:
            return self._registry[model_group]["capabilities"]
        return []

    def list_models(self) -> Dict[str, Any]:
        return dict(self._registry)

model_registry = ModelRegistry()