"""
Intelligent model routing and task classification for Sovereign AI Workbench.
Classifies tasks into precise capabilities and maps them to models.
"""

from typing import Dict, Any, Optional
from core.config import settings
from core.logging import logger
from llm.model_registry import model_registry


class ModelRouter:
    """Routes tasks to appropriate models based on required capabilities."""

    def __init__(self):
        """Initialize router mapping intents to model categories."""
        self.models = {
            "chat": getattr(settings, "OLLAMA_CHAT_MODEL", "qwen2.5:1.5b"),
            "coding": getattr(settings, "OLLAMA_CODE_MODEL", "qwen2.5-coder:1.5b"),
            "vision": getattr(settings, "OLLAMA_VISION_MODEL", "moondream:latest"),
            "embedding": getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text:latest"),
            "general_chat": getattr(settings, "OLLAMA_CHAT_MODEL", "qwen2.5:1.5b"),
            "code_task": getattr(settings, "OLLAMA_CODE_MODEL", "qwen2.5-coder:1.5b"),
            "vision/multimodal_task": getattr(settings, "OLLAMA_VISION_MODEL", "moondream:latest"),
            "file_operation": getattr(settings, "OLLAMA_CODE_MODEL", "qwen2.5-coder:1.5b"),
            "retrieval/memory_lookup": getattr(settings, "OLLAMA_CHAT_MODEL", "qwen2.5:1.5b"),
            "mixed/multi-step": getattr(settings, "OLLAMA_CHAT_MODEL", "qwen2.5:1.5b"),
        }

        self.capability_map = {
            "general_conversation": "general",
            "general_chat": "general",
            "general": "general",
            "chat": "general",
            "planning": "general",
            "risk_analysis": "general",
            "maintenance_analysis": "general",
            "safety_analysis": "general",
            "compliance": "general",
            "compliance_analysis": "general",
            "document_analysis": "general",
            "coding": "coding",
            "code_task": "coding",
            "python": "coding",
            "excel_processing": "coding",
            "file_automation": "coding",
            "file_operations": "coding",
            "file_operation": "coding",
            "tool_execution": "coding",
            "document_generation": "coding",
            "image_understanding": "vision",
            "visual_inspection": "vision",
            "vision_analysis": "vision",
            "vision/multimodal_task": "vision",
            "vision": "vision",
            "object_detection": "vision",
            "ocr": "python_ocr",  # Handled via tool, but tracked here
            "embeddings": "embedding",
            "embedding": "embedding",
            "retrieval/memory_lookup": "general",
            "mixed/multi-step": "general",
        }

        # Keywords for intent detection
        self.intent_keywords = {
            "image_understanding": ["image", "photo", "picture", "visual", "diagram", "screenshot", "chart"],
            "visual_inspection": ["inspect image", "anomaly in picture", "visual inspection"],
            "ocr": ["extract text", "extract all text", "scanned document", "scan document", "read text from image", "ocr"],
            "coding": ["code", "javascript", "java", "c++", "cpp", "c#", "rust", "go", "function", "debug"],
            "python": ["python", "pandas", "script"],
            "excel_processing": ["excel", "csv", "spreadsheet", "openpyxl", "dataframe"],
            "file_automation": ["file operations", "create folder", "create a folder", "delete file", "move file", "rename file", "list files", "write file", "save to file", "folder", "directory", "mkdir"],
            "risk_analysis": ["risk", "hazard", "severity", "mitigation"],
            "maintenance_analysis": ["maintenance", "equipment", "failure analysis", "incidents related to this equipment"],
            "safety_analysis": ["safety", "checklist", "sop analysis", "incident"],
            "compliance": ["compliance", "audit", "policy comparison"],
            "planning": ["plan", "step by step plan"],
            "embeddings": ["similarity search", "vector search"],
            "document_generation": ["create pdf", "modify pdf", "ppt", "powerpoint", "presentation", "create a file", "xlsx", "csv"],
            "object_detection": ["object detection", "detect objects", "bounding box", "detect object"]
        }

    def classify_task(self, message: str) -> str:
        """Classifies the task string into one of the capabilities."""
        msg_lower = (message or "").lower()

        # Check specific capabilities first
        for capability, keywords in self.intent_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                return capability

        # Default fallback
        return "general_conversation"

    def route(self, message: str, task_type: str = "auto", preferred_model: Optional[str] = None) -> str:
        """Route message to the optimal local model."""
        if preferred_model and preferred_model != "auto":
            return preferred_model

        if task_type == "auto":
            capability = self.classify_task(message)
        else:
            capability = task_type

        model_category = self.capability_map.get(capability, "general")

        if model_category == "python_ocr":
            # OCR is an agent/tool, not an LLM. Return a specific signal.
            return "PYTHON_OCR"

        model = model_registry.get_model(model_category)
        logger.info(f"[ROUTER] Classified task '{capability}' → category '{model_category}' → model={model}")
        return model

    def get_all_models(self) -> Dict[str, str]:
        """Return all available model mappings."""
        return dict(self.models)

    def get_roles(self) -> Dict[str, str]:
        """Return primary role-based model configurations."""
        return {
            "chat": self.models.get("chat", model_registry.get_model("general")),
            "coding": self.models.get("coding", model_registry.get_model("coding")),
            "vision": self.models.get("vision", model_registry.get_model("vision")),
            "embedding": self.models.get("embedding", model_registry.get_model("embedding"))
        }

    def set_role(self, role: str, model_name: str):
        """Update active model assignment for a given role."""
        if role in ["chat", "coding", "vision", "embedding"]:
            self.models[role] = model_name
            if role == "chat":
                self.models["general_chat"] = model_name
                self.models["retrieval/memory_lookup"] = model_name
                self.models["mixed/multi-step"] = model_name
                if "general" in model_registry._registry:
                    model_registry._registry["general"]["model"] = model_name
            elif role == "coding":
                self.models["code_task"] = model_name
                self.models["file_operation"] = model_name
                if "coding" in model_registry._registry:
                    model_registry._registry["coding"]["model"] = model_name
            elif role == "vision":
                self.models["vision/multimodal_task"] = model_name
                if "vision" in model_registry._registry:
                    model_registry._registry["vision"]["model"] = model_name
            elif role == "embedding":
                if "embedding" in model_registry._registry:
                    model_registry._registry["embedding"]["model"] = model_name
            logger.info(f"[ROUTER] Configured role '{role}' -> '{model_name}'")


# Global singleton router
model_router = ModelRouter()
