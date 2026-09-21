"""
Centralized SLM Model Registry for Sovereign AI Workbench.

8-9 Model SLM Specialist Architecture:
- router: qwen3:0.6b (fallback: qwen2.5:0.5b, then qwen2.5:1.5b)
- general: qwen2.5:0.5b (fallback: qwen2.5:1.5b)
- planner: llama3.2:1b (fallback: qwen2.5:1.5b)
- document: gemma3:1b (fallback: qwen2.5:1.5b)
- coding: qwen2.5-coder:1.5b (fallback: qwen2.5-coder:0.5b, then qwen2.5:1.5b)
- risk: qwen2.5:1.5b (fallback: qwen2.5:0.5b)
- compliance: qwen2.5:1.5b (fallback: qwen2.5:0.5b)
- safety: qwen2.5:1.5b (fallback: qwen2.5:0.5b)
- maintenance: qwen2.5:1.5b (fallback: qwen2.5:0.5b)
- reporting: qwen2.5:1.5b (fallback: qwen2.5:0.5b)
- critic: smollm2:1.7b (fallback: qwen2.5:0.5b, then qwen2.5:1.5b)
- vision: moondream (fallback: moondream:latest, qwen2.5vl:3b)
- embedding: nomic-embed-text (fallback: nomic-embed-text:latest)

Key Principles:
- Single source of truth for model names and specialist roles.
- Dynamic Ollama installed model detection.
- Graceful fallbacks so the system never crashes if a model is missing.
- Administrator reconfigurability.
- Multiple logical specialist roles can safely map to the same physical SLM.
- CPU-first execution (single model active per inference step).
"""

from copy import deepcopy
from typing import Optional, Dict, Any, List
import httpx

from core.logging import logger
from core.config import settings


# ============================================================
# SPECIALIST SLM DEFINITION REGISTRY
# ============================================================

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "router": {
        "provider": "ollama",
        "model": "qwen3:0.6b",
        "fallbacks": ["qwen2.5:0.5b", "qwen2.5:1.5b"],
        "capabilities": ["intent_classification", "routing", "structured_json"],
        "description": "Fast deterministic/SLM request routing & intent classification",
        "tool_calling": False,
    },
    "general": {
        "provider": "ollama",
        "model": "qwen2.5:0.5b",
        "fallbacks": ["qwen2.5:1.5b"],
        "capabilities": ["general_qa", "chat", "rewrite", "reasoning"],
        "description": "General conversational assistance and text synthesis",
        "tool_calling": True,
    },
    "planner": {
        "provider": "ollama",
        "model": "llama3.2:1b",
        "fallbacks": ["qwen2.5:1.5b", "qwen2.5:0.5b"],
        "capabilities": ["planning", "reasoning", "task_decomposition"],
        "description": "Step-by-step industrial execution plan generation",
        "tool_calling": True,
    },
    "document": {
        "provider": "ollama",
        "model": "gemma3:1b",
        "fallbacks": ["qwen2.5:1.5b", "qwen2.5:0.5b"],
        "capabilities": ["document_analysis", "structured_extraction", "summarization"],
        "description": "Deep document comprehension, table and text extraction",
        "tool_calling": True,
    },
    "coding": {
        "provider": "ollama",
        "model": "qwen2.5-coder:1.5b",
        "fallbacks": ["qwen2.5-coder:0.5b", "qwen2.5:1.5b"],
        "capabilities": ["coding", "debugging", "automation", "python", "scripting"],
        "description": "Code generation, sandbox automation, script execution",
        "tool_calling": True,
    },
    "risk": {
        "provider": "ollama",
        "model": "qwen2.5:1.5b",
        "fallbacks": ["qwen2.5:0.5b"],
        "capabilities": ["risk_analysis", "hazard_identification", "mitigation_planning"],
        "description": "Industrial hazard, severity matrix and risk quantification",
        "tool_calling": True,
    },
    "compliance": {
        "provider": "ollama",
        "model": "qwen2.5:1.5b",
        "fallbacks": ["qwen2.5:0.5b"],
        "capabilities": ["compliance", "policy_analysis", "sop_verification", "audit"],
        "description": "ISO/OSHA standards adherence and regulatory verification",
        "tool_calling": True,
    },
    "safety": {
        "provider": "ollama",
        "model": "qwen2.5:1.5b",
        "fallbacks": ["qwen2.5:0.5b"],
        "capabilities": ["safety_analysis", "osha_guidelines", "hazard_mitigation"],
        "description": "Industrial plant safety inspection and protocol checking",
        "tool_calling": True,
    },
    "maintenance": {
        "provider": "ollama",
        "model": "qwen2.5:1.5b",
        "fallbacks": ["qwen2.5:0.5b"],
        "capabilities": ["maintenance_analysis", "equipment_diagnosis", "telemetry_analysis"],
        "description": "Equipment health, vibration/thermal telemetry diagnosis",
        "tool_calling": True,
    },
    "reporting": {
        "provider": "ollama",
        "model": "qwen2.5:1.5b",
        "fallbacks": ["qwen2.5:0.5b"],
        "capabilities": ["report_generation", "executive_summary", "structured_synthesis"],
        "description": "Technical report synthesis, formatting and documentation",
        "tool_calling": True,
    },
    "critic": {
        "provider": "ollama",
        "model": "smollm2:1.7b",
        "fallbacks": ["qwen2.5:0.5b", "qwen2.5:1.5b"],
        "capabilities": ["verification", "critique", "hallucination_check"],
        "description": "Factual verification, evidence cross-checking and critique",
        "tool_calling": False,
    },
    "vision": {
        "provider": "ollama",
        "model": "moondream",
        "fallbacks": ["moondream:latest", "qwen2.5vl:3b"],
        "capabilities": ["image_understanding", "visual_inspection"],
        "description": "Visual scene analysis and component inspection",
        "tool_calling": False,
    },
    "embedding": {
        "provider": "ollama",
        "model": "nomic-embed-text",
        "fallbacks": ["nomic-embed-text:latest"],
        "capabilities": ["embedding", "semantic_search", "rag"],
        "description": "High-density 768-dimensional local text embeddings",
        "tool_calling": False,
    },
}


# ============================================================
# AGENT -> SPECIALIST ROLE MAPPING
# ============================================================

AGENT_ROLE_MAP: Dict[str, str] = {
    # General
    "general": "general",
    "general_assistant": "general",
    "general_chat": "general",
    "chat": "general",

    # Router & Planner
    "router": "router",
    "router_agent": "router",
    "planner": "planner",
    "planner_agent": "planner",

    # Specialists
    "document": "document",
    "document_agent": "document",
    "document_crud": "document",
    "document_generation": "document",
    "document_generation_agent": "document",
    "document_specialist": "document",
    "coding": "coding",
    "coding_agent": "coding",
    "code_agent": "coding",
    "risk": "risk",
    "risk_agent": "risk",
    "risk_analysis": "risk",
    "compliance": "compliance",
    "compliance_agent": "compliance",
    "safety": "safety",
    "safety_agent": "safety",
    "maintenance": "maintenance",
    "maintenance_agent": "maintenance",
    "reporting": "reporting",
    "reporting_agent": "reporting",
    "critic": "critic",
    "critic_agent": "critic",
    "verifier": "critic",
    "verifier_agent": "critic",

    # Vision & Multimodal
    "vision": "vision",
    "vision_agent": "vision",
    "ocr": "document",
    "ocr_agent": "document",

    # Knowledge & RAG
    "knowledge": "embedding",
    "knowledge_agent": "embedding",
    "rag": "embedding",
    "memory": "embedding",
    "memory_agent": "embedding",

    # Filesystem & Automation
    "filesystem": "coding",
    "filesystem_agent": "coding",
    "spreadsheet": "reporting",
    "spreadsheet_agent": "reporting",
    "ppt": "reporting",
    "ppt_agent": "reporting",
}


# ============================================================
# MODEL REGISTRY CLASS
# ============================================================

class ModelRegistry:
    """Centralized SLM Model Registry with dynamic fallback resolution."""

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, Any]] = deepcopy(MODEL_REGISTRY)
        self._agent_roles: Dict[str, str] = deepcopy(AGENT_ROLE_MAP)
        self._installed_models: List[str] = []
        self._resolved_cache: Dict[str, str] = {}

    def _normalize_name(self, name: str) -> str:
        return (name or "").strip().lower()

    def update_installed_models(self, models: List[str]) -> None:
        """Update list of currently installed models from Ollama."""
        self._installed_models = [self._normalize_name(m) for m in models if m]
        self._resolved_cache.clear()
        logger.info(f"[MODEL_REGISTRY] Updated installed models: {self._installed_models}")

    async def detect_installed_models(self) -> List[str]:
        """Query Ollama for installed models and update registry state."""
        try:
            from llm.ollama_client import ollama_client
            models = await ollama_client.get_available_models()
            self.update_installed_models(models)
            return self._installed_models
        except Exception as e:
            logger.warning(f"[MODEL_REGISTRY] Failed to detect installed models: {e}")
            return self._installed_models

    def get_installed_models(self) -> List[str]:
        """Return list of currently cached installed models."""
        return list(self._installed_models)

    def is_installed(self, model_name: str) -> bool:
        """Check if a specific model or base model is installed in Ollama."""
        if not self._installed_models:
            return True  # If not yet probed, assume available until probed


        norm = self._normalize_name(model_name)
        if norm in self._installed_models:
            return True

        # Check with or without :latest
        if ":latest" in norm:
            base = norm.replace(":latest", "")
            if base in self._installed_models:
                return True
        else:
            if f"{norm}:latest" in self._installed_models:
                return True

        # Check prefix match if base matches
        req_base = norm.split(":")[0]
        for inst in self._installed_models:
            if inst == norm or inst.split(":")[0] == req_base:
                return True

        return False

    def get_role_for_agent(self, agent_name: str) -> str:
        """Map an agent slug to a specialist model role."""
        norm = self._normalize_name(agent_name)
        return self._agent_roles.get(norm, "general")

    def resolve_model(self, role: str) -> str:
        """
        Resolve the effective model for a specialist role with graceful fallback.
        Never crashes if the primary model is uninstalled.
        """
        role_key = self._normalize_name(role)
        if role_key in self._resolved_cache:
            return self._resolved_cache[role_key]

        config = self._registry.get(role_key)
        if not config:
            role_key = self.get_role_for_agent(role_key)
            config = self._registry.get(role_key, self._registry["general"])

        primary_model = config["model"]
        candidates = [primary_model] + list(config.get("fallbacks", []))

        # Check candidates in order
        chosen_model = None
        for candidate in candidates:
            if self.is_installed(candidate):
                chosen_model = candidate
                break

        # Fallback to general model if none of the role candidates are installed
        if not chosen_model:
            logger.warning(
                f"[MODEL_REGISTRY] Primary '{primary_model}' and fallbacks {config.get('fallbacks', [])} "
                f"for role '{role_key}' are not installed. Falling back to general model."
            )
            for gen_candidate in [self._registry["general"]["model"]] + self._registry["general"].get("fallbacks", []):
                if self.is_installed(gen_candidate):
                    chosen_model = gen_candidate
                    break
            if not chosen_model:
                chosen_model = primary_model  # Default to declared primary

        self._resolved_cache[role_key] = chosen_model
        return chosen_model

    def get_model(self, task_type_or_role: str = "general") -> str:
        """Alias for resolving model by role or agent."""
        return self.resolve_model(task_type_or_role)

    def get_agent_model(
        self,
        task_type: str = "general",
        requested_model: Optional[str] = None
    ) -> str:
        """Get model for agent, respecting explicit requested model if provided."""
        if requested_model and requested_model.strip().lower() != "auto":
            return requested_model.strip()

        role = self.get_role_for_agent(task_type)
        return self.resolve_model(role)

    def get_model_config(self, role_or_model: str) -> Optional[Dict[str, Any]]:
        """Retrieve model configuration for role or model name."""
        norm = self._normalize_name(role_or_model)
        if norm in self._registry:
            cfg = deepcopy(self._registry[norm])
            cfg["effective_model"] = self.resolve_model(norm)
            cfg["installed"] = self.is_installed(cfg["model"])
            return cfg

        for role, cfg in self._registry.items():
            if self._normalize_name(cfg.get("model", "")) == norm:
                res = deepcopy(cfg)
                res["effective_model"] = self.resolve_model(role)
                res["installed"] = self.is_installed(norm)
                return res

        return None

    def get_model_capabilities(self, role: str) -> List[str]:
        """Return capabilities for a specialist role."""
        cfg = self.get_model_config(role)
        return list(cfg.get("capabilities", [])) if cfg else []

    def has_capability(self, role: str, capability: str) -> bool:
        """Check whether role or model has a specific capability."""
        caps = [c.lower() for c in self.get_model_capabilities(role)]
        return self._normalize_name(capability) in caps

    def supports_tools(self, model_name_or_role: str) -> bool:
        """Check if model supports structured tool execution."""
        cfg = self.get_model_config(model_name_or_role)
        if cfg:
            return bool(cfg.get("tool_calling", False))
        return False

    def set_role_model(self, role: str, model_name: str) -> None:
        """Administrator configuration: override model assignment for a role."""
        role_key = self._normalize_name(role)
        if role_key in self._registry:
            self._registry[role_key]["model"] = model_name.strip()
            self._resolved_cache.pop(role_key, None)
            logger.info(f"[MODEL_REGISTRY] Overrode role '{role_key}' with model '{model_name}'")

    def list_models(self) -> Dict[str, Any]:
        """Return all specialist roles with availability and effective model."""
        res = {}
        for role, cfg in self._registry.items():
            effective = self.resolve_model(role)
            res[role] = {
                "configured_model": cfg["model"],
                "effective_model": effective,
                "fallbacks": cfg.get("fallbacks", []),
                "installed": self.is_installed(cfg["model"]),
                "effective_installed": self.is_installed(effective),
                "capabilities": cfg.get("capabilities", []),
                "tool_calling": cfg.get("tool_calling", False),
                "description": cfg.get("description", "")
            }
        return res

    def list_agents(self) -> Dict[str, Any]:
        """Return agent-to-role mappings."""
        res = {}
        for agent, role in self._agent_roles.items():
            res[agent] = {
                "role": role,
                "model": self.resolve_model(role),
                "capabilities": self.get_model_capabilities(role)
            }
        return res

    def get_route_info(
        self,
        task_type: str = "general",
        requested_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provide routing metadata for request tracking."""
        role = self.get_role_for_agent(task_type)
        model = self.get_agent_model(task_type=task_type, requested_model=requested_model)
        cfg = self.get_model_config(role) or self._registry["general"]

        return {
            "task_type": task_type,
            "agent": task_type,
            "role": role,
            "model": model,
            "provider": cfg.get("provider", "ollama"),
            "tool_calling": self.supports_tools(role),
            "capabilities": cfg.get("capabilities", [])
        }


# Global singleton instance
model_registry = ModelRegistry()