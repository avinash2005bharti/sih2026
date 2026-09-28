"""
Model Registry for Sovereign AI Workbench.
SIH 26117 — Dual Hardware Aware (RTX 2050 4GB GPU & CPU-Only Profiles).

Hardware verified 2026-09-25:
  GPU: NVIDIA RTX 2050 4GB
  Installed models: qwen3:0.6b, qwen3:1.7b, qwen3:4b, qwen2.5:0.5b, qwen2.5:1.5b,
                    qwen2.5-coder:1.5b, qwen2.5-coder:3b, qwen3-vl:4b, qwen2.5vl:3b,
                    nomic-embed-text:latest
"""

from typing import Dict, Any, List, Optional
from copy import deepcopy
from pydantic import BaseModel, Field
import httpx

from core.logging import logger
from core.config import settings
from core.hardware import get_hardware_profile, PROFILE_GPU_RTX2050, PROFILE_CPU_ONLY


class ModelMetadata(BaseModel):
    """Structured metadata for local AI models."""
    name: str = Field(..., description="Ollama model tag or identifier")
    provider: str = Field(default="ollama", description="Local provider: ollama or local")
    endpoint: str = Field(default="http://127.0.0.1:11434", description="Provider endpoint")
    type: str = Field(default="llm", description="Model category: llm, vlm, embedding, classifier")
    role: List[str] = Field(default_factory=list, description="Supported roles")
    capabilities: List[str] = Field(default_factory=list, description="Detailed capabilities")
    task_types: List[str] = Field(default_factory=list, description="Primary task types")
    modality: str = Field(default="text", description="Modality: text, multimodal, embedding")
    context_length: int = Field(default=32768, description="Context window size")
    hardware: List[str] = Field(default_factory=lambda: ["gpu", "cpu"], description="Supported hardware profiles")
    vision: bool = Field(default=False, description="Supports multimodal visual inputs")
    tools: bool = Field(default=False, description="Supports tool/function calling")
    embedding: bool = Field(default=False, description="Produces vector embeddings")
    enabled: bool = Field(default=True, description="Whether the model is enabled for routing")
    priority: int = Field(default=1, description="Selection priority (lower = higher priority)")
    fallback_model: Optional[str] = Field(default=None, description="Primary fallback model name")
    temperature: float = Field(default=0.7, description="Default sampling temperature")
    timeout: float = Field(default=60.0, description="Inference timeout in seconds")
    vram_estimate_mb: int = Field(default=2000, description="Approximate VRAM usage in MB")
    gpu_suitability: str = Field(default="ideal", description="GPU suitability on RTX 2050")
    description: str = Field(default="", description="Human-readable description")


# ============================================================
# MASTER MODEL DEFINITIONS (SIH 26117 Centralized Model Registry)
# ============================================================

ALL_MODELS: Dict[str, Dict[str, Any]] = {
    # ─── Ultra-fast Fallback / Routing / Greetings ──────────
    "qwen2.5:0.5b": {
        "name": "qwen2.5:0.5b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "classifier",
        "role": ["fallback", "simple", "greeting", "classifier", "router"],
        "capabilities": ["classification", "routing", "greetings", "trivial_response"],
        "task_types": ["SIMPLE_GREETING", "TRIVIAL_CLASSIFICATION"],
        "modality": "text",
        "context_length": 32768,
        "hardware": ["gpu", "cpu"],
        "vision": False,
        "tools": False,
        "embedding": False,
        "enabled": True,
        "priority": 1,
        "fallback_model": None,
        "temperature": 0.2,
        "timeout": 30.0,
        "vram_estimate_mb": 400,
        "gpu_suitability": "ideal",
        "description": "Ultra-fast classification / simple routing / greetings (397MB) ✅ keep warm"
    },

    # ─── Lightweight Intent Classifier / Extraction ────────
    "qwen3:0.6b": {
        "name": "qwen3:0.6b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "classifier",
        "role": ["classifier", "router", "extractor"],
        "capabilities": ["intent_classification", "routing", "structured_json", "simple_extraction"],
        "task_types": ["INTENT_CLASSIFICATION", "ROUTING", "STRUCTURED_EXTRACTION"],
        "modality": "text",
        "context_length": 32768,
        "hardware": ["gpu", "cpu"],
        "vision": False,
        "tools": False,
        "embedding": False,
        "enabled": True,
        "priority": 1,
        "fallback_model": "qwen2.5:0.5b",
        "temperature": 0.1,
        "timeout": 30.0,
        "vram_estimate_mb": 600,
        "gpu_suitability": "ideal",
        "description": "Lightweight intent classification / simple extraction (522MB) ✅ keep warm"
    },

    # ─── General Chat / Industrial Q&A ────────────────────
    "qwen2.5:1.5b": {
        "name": "qwen2.5:1.5b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "llm",
        "role": ["general", "chat", "spreadsheet"],
        "capabilities": ["general_chat", "industrial_qa", "explanations", "concept_analysis"],
        "task_types": ["GENERAL_CHAT", "CONCEPT_EXPLANATION", "GENERAL_INDUSTRIAL_QA"],
        "modality": "text",
        "context_length": 32768,
        "hardware": ["gpu", "cpu"],
        "vision": False,
        "tools": True,
        "embedding": False,
        "enabled": True,
        "priority": 1,
        "fallback_model": "qwen3:1.7b",
        "temperature": 0.7,
        "timeout": 60.0,
        "vram_estimate_mb": 1000,
        "gpu_suitability": "ideal",
        "description": "Normal general chat and industrial Q&A (986MB) ✅ keep warm"
    },

    # ─── Lightweight Reasoning / Fallback Reasoning ────────
    "qwen3:1.7b": {
        "name": "qwen3:1.7b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "llm",
        "role": ["lightweight_reasoning", "fallback_reasoning", "planner"],
        "capabilities": ["lightweight_reasoning", "fallback_reasoning", "intermediate_synthesis"],
        "task_types": ["LIGHTWEIGHT_REASONING", "FALLBACK_REASONING"],
        "modality": "text",
        "context_length": 32768,
        "hardware": ["gpu", "cpu"],
        "vision": False,
        "tools": True,
        "embedding": False,
        "enabled": True,
        "priority": 2,
        "fallback_model": "qwen2.5:1.5b",
        "temperature": 0.3,
        "timeout": 60.0,
        "vram_estimate_mb": 1400,
        "gpu_suitability": "good",
        "description": "Lightweight reasoning and fallback reasoning (1.4GB) ✅"
    },

    # ─── Advanced Agentic Planning, Research & Reasoning ───
    "qwen3:4b": {
        "name": "qwen3:4b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "llm",
        "role": [
            "reasoning", "planner", "document", "document_qa", "document_summary",
            "reporting", "maintenance", "safety", "compliance", "risk", "research"
        ],
        "capabilities": [
            "planning", "task_decomposition", "advanced_planning", "research", "document_reasoning", "reporting",
            "maintenance_analysis", "safety_analysis", "compliance_analysis", "risk_analysis"
        ],
        "task_types": [
            "DOCUMENT_QA", "DOCUMENT_SUMMARY", "MULTI_DOCUMENT_RESEARCH",
            "MAINTENANCE_ANALYSIS", "SAFETY_ANALYSIS", "COMPLIANCE_ANALYSIS",
            "RISK_ANALYSIS", "REPORTING", "PDF_PLANNING"
        ],
        "modality": "text",
        "context_length": 32768,
        "hardware": ["gpu", "cpu"],
        "vision": False,
        "tools": True,
        "embedding": False,
        "enabled": True,
        "priority": 1,
        "fallback_model": "qwen3:1.7b",
        "temperature": 0.2,
        "timeout": 180.0,
        "vram_estimate_mb": 2600,
        "gpu_suitability": "managed",
        "description": "Advanced agentic planning, research, document reasoning, reporting (2.5GB) ✅"
    },

    # ─── Coding Specialist ─────────────────────────────────
    "qwen2.5-coder:1.5b": {
        "name": "qwen2.5-coder:1.5b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "llm",
        "role": ["coding", "tool_execution"],
        "capabilities": ["coding", "python", "javascript", "typescript", "debugging", "code_generation"],
        "task_types": ["CODE_GENERATION", "CODE_EXECUTION", "DEBUGGING"],
        "modality": "text",
        "context_length": 32768,
        "hardware": ["gpu", "cpu"],
        "vision": False,
        "tools": True,
        "embedding": False,
        "enabled": True,
        "priority": 1,
        "fallback_model": "qwen2.5-coder:3b",
        "temperature": 0.1,
        "timeout": 90.0,
        "vram_estimate_mb": 1100,
        "gpu_suitability": "ideal",
        "description": "Specialist coding model for scripting and code generation (986MB) ✅"
    },

    # ─── Complex Coding Fallback / Benchmark ───────────────
    "qwen2.5-coder:3b": {
        "name": "qwen2.5-coder:3b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "llm",
        "role": ["coding_heavy", "complex_code", "tool_execution_heavy"],
        "capabilities": ["coding", "complex_coding", "refactoring", "multi_file_coding", "benchmark"],
        "task_types": ["COMPLEX_CODE", "CODE_BENCHMARK", "HEAVY_REFACTORING"],
        "modality": "text",
        "context_length": 32768,
        "hardware": ["gpu"],
        "vision": False,
        "tools": True,
        "embedding": False,
        "enabled": True,
        "priority": 2,
        "fallback_model": "qwen2.5-coder:1.5b",
        "temperature": 0.1,
        "timeout": 120.0,
        "vram_estimate_mb": 2100,
        "gpu_suitability": "managed",
        "description": "Complex coding fallback and heavy software engineering (1.9GB) ✅"
    },

    # ─── Primary Vision Model ──────────────────────────────
    "qwen3-vl:4b": {
        "name": "qwen3-vl:4b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "vlm",
        "role": ["vision", "image_understanding"],
        "capabilities": ["image_understanding", "component_identification", "visual_inspection", "diagrams"],
        "task_types": ["IMAGE_UNDERSTANDING", "VISUAL_INSPECTION", "COMPONENT_IDENTIFICATION"],
        "modality": "multimodal",
        "context_length": 32768,
        "hardware": ["gpu", "cpu"],
        "vision": True,
        "tools": False,
        "embedding": False,
        "enabled": True,
        "priority": 1,
        "fallback_model": "qwen2.5vl:3b",
        "temperature": 0.2,
        "timeout": 120.0,
        "vram_estimate_mb": 3300,
        "gpu_suitability": "managed",
        "description": "Primary multimodal vision model for industrial inspection and diagram understanding (3.3GB) ✅"
    },

    # ─── Vision Fallback Model ─────────────────────────────
    "qwen2.5vl:3b": {
        "name": "qwen2.5vl:3b",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "vlm",
        "role": ["vision_fallback", "vision"],
        "capabilities": ["image_understanding", "visual_inspection", "vision_fallback"],
        "task_types": ["VISION_FALLBACK", "IMAGE_UNDERSTANDING_FALLBACK"],
        "modality": "multimodal",
        "context_length": 32768,
        "hardware": ["gpu", "cpu"],
        "vision": True,
        "tools": False,
        "embedding": False,
        "enabled": True,
        "priority": 2,
        "fallback_model": None,
        "temperature": 0.2,
        "timeout": 90.0,
        "vram_estimate_mb": 3200,
        "gpu_suitability": "managed",
        "description": "Vision fallback model — reliable fast multimodal inference (3.2GB) ✅"
    },

    # ─── Embeddings Only ───────────────────────────────────
    "nomic-embed-text": {
        "name": "nomic-embed-text",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "embedding",
        "role": ["embedding", "rag"],
        "capabilities": ["embeddings", "vector_indexing", "semantic_search"],
        "task_types": ["EMBEDDING", "SEMANTIC_SEARCH", "RAG_INDEXING"],
        "modality": "embedding",
        "context_length": 8192,
        "hardware": ["gpu", "cpu"],
        "vision": False,
        "tools": False,
        "embedding": True,
        "enabled": True,
        "priority": 1,
        "fallback_model": "nomic-embed-text:latest",
        "temperature": 0.0,
        "timeout": 60.0,
        "vram_estimate_mb": 300,
        "gpu_suitability": "ideal",
        "description": "768-dim embeddings for Qdrant vector retrieval and document RAG (274MB) ✅ keep warm"
    },
    "nomic-embed-text:latest": {
        "name": "nomic-embed-text:latest",
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
        "type": "embedding",
        "role": ["embedding", "rag"],
        "capabilities": ["embeddings", "vector_indexing", "semantic_search"],
        "task_types": ["EMBEDDING", "SEMANTIC_SEARCH", "RAG_INDEXING"],
        "modality": "embedding",
        "context_length": 8192,
        "hardware": ["gpu", "cpu"],
        "vision": False,
        "tools": False,
        "embedding": True,
        "enabled": True,
        "priority": 1,
        "fallback_model": "nomic-embed-text",
        "temperature": 0.0,
        "timeout": 60.0,
        "vram_estimate_mb": 300,
        "gpu_suitability": "ideal",
        "description": "768-dim text embeddings for RAG and vector memory (274MB) ✅ keep warm"
    },
}


class ModelRegistry:
    """Centralized SLM Model Registry supporting dual hardware profiles."""

    def __init__(self) -> None:
        self._models: Dict[str, ModelMetadata] = {
            k: ModelMetadata(**v) for k, v in ALL_MODELS.items()
        }
        self._installed_models: List[str] = []
        self._resolved_cache: Dict[str, str] = {}

    def _normalize_name(self, name: str) -> str:
        return (name or "").strip().lower()

    def detect_installed_models_sync(self) -> List[str]:
        """Synchronously query local Ollama API for installed models."""
        if self._installed_models:
            return self._installed_models
        try:
            import urllib.request, json
            base_url = (settings.OLLAMA_BASE_URL or "http://127.0.0.1:11434").replace("localhost", "127.0.0.1").rstrip("/")
            req = urllib.request.Request(f"{base_url}/api/tags", headers={"User-Agent": "SovereignAI/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode())
                models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                if models:
                    self.update_installed_models(models)
        except Exception as e:
            logger.debug(f"[MODEL_REGISTRY] Sync probe error: {e}")
        return self._installed_models

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
            return self.detect_installed_models_sync()

    def get_installed_models(self) -> List[str]:
        """Return list of currently cached installed models."""
        if not self._installed_models:
            self.detect_installed_models_sync()
        return list(self._installed_models)

    def is_installed(self, model_name: str) -> bool:
        """Check if a specific model is installed in local Ollama."""
        if not self._installed_models:
            self.detect_installed_models_sync()

        if not self._installed_models:
            return False

        norm = self._normalize_name(model_name)
        if norm in self._installed_models:
            return True

        if ":latest" in norm:
            base = norm.replace(":latest", "")
            if base in self._installed_models or f"{base}:latest" in self._installed_models:
                return True
        else:
            if f"{norm}:latest" in self._installed_models:
                return True

        return False

    def get_model_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        norm = self._normalize_name(model_name)
        for key, meta in self._models.items():
            if key == norm or f"{key}:latest" == norm or norm.startswith(key):
                return meta
        return None

    def list_models(self, hardware_profile: Optional[str] = None) -> List[ModelMetadata]:
        """List models, optionally filtered by hardware profile (gpu/cpu)."""
        hw = (hardware_profile or get_hardware_profile()).lower()
        is_gpu = "gpu" in hw

        results = []
        for m in self._models.values():
            if is_gpu or "cpu" in m.hardware:
                results.append(m)
        return results

    def get_role_for_agent(self, agent_name: str) -> str:
        """Map specialist agent name or task type to a core model role."""
        name = (agent_name or "").lower().strip()
        mapping = {
            # Coding agents
            "code_agent": "coding",
            "coding": "coding",
            "coder": "coding",
            "code_generation": "coding",
            "code_execution": "coding",
            "filesystem_agent": "coding",
            "complex_coding": "coding_heavy",
            "complex_code": "coding_heavy",

            # Vision agents
            "vision_agent": "vision",
            "vision": "vision",
            "image_analysis": "vision",
            "image_understanding": "vision",
            "ocr": "ocr",
            "ocr_agent": "ocr",

            # Classifier / router
            "classifier": "classifier",
            "router": "router",

            # Embedding
            "embedding": "embedding",
            "rag": "embedding",

            # Planner
            "planner": "planner",

            # Industrial specialist agents → reasoning (qwen3:1.7b)
            "document_agent": "reasoning",
            "document": "reasoning",
            "document_qa": "reasoning",
            "document_summary": "reasoning",
            "research_agent": "reasoning",
            "research": "reasoning",
            "multi_document_research": "reasoning",
            "reporting_agent": "reasoning",
            "reporting": "reasoning",
            "risk_agent": "reasoning",
            "risk": "reasoning",
            "compliance_agent": "reasoning",
            "compliance": "reasoning",
            "maintenance_agent": "reasoning",
            "maintenance": "reasoning",
            "safety_agent": "reasoning",
            "safety": "reasoning",
            "knowledge_agent": "reasoning",
            "reasoning": "reasoning",

            # Spreadsheet / Excel -> spreadsheet (uses qwen2.5:1.5b for conversation/planning + openpyxl tool, NEVER coder!)
            "spreadsheet_agent": "spreadsheet",
            "spreadsheet": "spreadsheet",
            "excel": "spreadsheet",
            "excel_generation": "spreadsheet",
            "data_analysis": "spreadsheet",

            # Simple / greeting / fallback
            "simple": "fallback",
            "greeting": "fallback",
            "fallback": "fallback",

            # General assistant / chat
            "general_assistant": "general",
            "general": "general",
            "chat": "general",
        }
        return mapping.get(name, "general")

    def get_default_model_for_role(self, role: str, hardware_profile: Optional[str] = None) -> str:
        """Return the default model tag for a given role based on hardware profile."""
        hw = (hardware_profile or get_hardware_profile()).upper()
        is_gpu = "GPU" in hw or hw == PROFILE_GPU_RTX2050

        r = (role or "").lower().strip()
        if hasattr(self, "_role_overrides") and r in self._role_overrides:
            return self._role_overrides[r]

        if is_gpu:
            if r in ["classifier", "router"]:
                return getattr(settings, "GPU_CLASSIFIER_MODEL", "qwen3:0.6b")
            elif r in ["planner"]:
                return getattr(settings, "GPU_PLANNER_MODEL", "qwen3:1.7b")
            elif r in ["reasoning", "document", "document_qa", "document_summary", "reporting", "maintenance", "safety", "compliance", "risk", "research"]:
                return getattr(settings, "GPU_REASONING_MODEL", "qwen3:1.7b")
            elif r in ["coding", "tool_execution"]:
                return getattr(settings, "GPU_CODER_MODEL", "qwen2.5-coder:1.5b")
            elif r in ["coding_heavy", "complex_code"]:
                return getattr(settings, "GPU_CODER_HEAVY_MODEL", "qwen2.5-coder:3b")
            elif r in ["vision", "image_analysis", "image_understanding"]:
                return getattr(settings, "GPU_VISION_MODEL", "qwen2.5vl:3b")
            elif r in ["vision_fallback"]:
                return getattr(settings, "GPU_VISION_FALLBACK", "qwen2.5vl:3b")
            elif r in ["embedding", "rag"]:
                return getattr(settings, "EMBEDDING_MODEL", "nomic-embed-text")
            elif r in ["fallback", "simple", "greeting"]:
                return getattr(settings, "GPU_FALLBACK_MODEL", "qwen2.5:0.5b")
            elif r in ["spreadsheet"]:
                return getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b")
            else:  # general
                return getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b")
        else:
            if r in ["classifier", "router"]:
                return getattr(settings, "CPU_CLASSIFIER_MODEL", "qwen2.5:0.5b")
            elif r in ["planner", "reasoning"]:
                return "qwen3:1.7b"
            elif r in ["coding", "tool_execution"]:
                return getattr(settings, "CPU_CODER_MODEL", "qwen2.5-coder:1.5b")
            elif r in ["vision", "image_analysis"]:
                return getattr(settings, "CPU_VISION_MODEL", "qwen2.5vl:3b")
            elif r in ["embedding", "rag"]:
                return getattr(settings, "EMBEDDING_MODEL", "nomic-embed-text")
            elif r in ["fallback", "simple", "greeting"]:
                return getattr(settings, "CPU_CLASSIFIER_MODEL", "qwen2.5:0.5b")
            else:
                return getattr(settings, "CPU_MAIN_MODEL", "qwen2.5:1.5b")

    def set_role_model(self, role: str, model_name: str) -> None:
        """Admin or runtime override of model assigned to a role."""
        if not hasattr(self, "_role_overrides"):
            self._role_overrides = {}
        self._role_overrides[role.lower().strip()] = model_name
        self._resolved_cache.clear()
        logger.info(f"[MODEL_REGISTRY] Overrode role '{role}' -> '{model_name}'")

    def resolve_model(self, role_or_model: str, hardware_profile: Optional[str] = None) -> str:
        """
        Resolve a role name (e.g. 'coding', 'general', 'vision') or a model tag
        to an actually installed model in local Ollama via fallback chain.
        """
        if not role_or_model:
            role_or_model = "general"

        cache_key = f"{role_or_model}:{hardware_profile}"
        if cache_key in self._resolved_cache:
            return self._resolved_cache[cache_key]

        norm = self._normalize_name(role_or_model)
        known_roles = {
            "general", "planner", "reasoning", "coding", "tool_execution",
            "vision", "image_analysis", "ocr", "classifier", "router",
            "embedding", "rag", "document", "reporting", "safety", "maintenance",
            "compliance", "risk", "critic", "code_agent", "document_agent",
            "vision_agent", "risk_agent", "compliance_agent", "safety_agent",
            "maintenance_agent", "reporting_agent", "filesystem_agent",
            "fallback", "simple", "greeting", "general_assistant",
            "knowledge_agent", "spreadsheet_agent", "ppt_agent"
        }

        if norm in known_roles:
            target_role = self.get_role_for_agent(norm)
            candidate = self.get_default_model_for_role(target_role, hardware_profile)
        else:
            candidate = role_or_model

        resolved = self.resolve_fallback_chain(candidate)
        self._resolved_cache[cache_key] = resolved
        return resolved

    def get_agent_model(self, agent_name: str = "general", requested_model: Optional[str] = None) -> str:
        """Convenience method for agent initialization."""
        if requested_model and requested_model != "auto":
            return self.resolve_model(requested_model)
        role = self.get_role_for_agent(agent_name)
        return self.resolve_model(role)

    def get_model(self, role_or_agent: str = "general") -> "ModelString":
        """Convenience alias for resolve_model returning rich string with metadata properties."""
        resolved = self.resolve_model(role_or_agent)
        meta = self.get_model_metadata(role_or_agent) or self.get_model_metadata(resolved)
        return ModelString(resolved, meta)

    def estimate_vram_mb(self, model_names: List[str]) -> int:
        """Estimate total VRAM needed for a set of models."""
        total = 0
        for name in model_names:
            meta = self.get_model_metadata(name)
            total += meta.vram_estimate_mb if meta else 2000
        return total

    def get_fallback(self, model_name: str) -> Optional[str]:
        """Get the configured fallback model name for a given model."""
        meta = self.get_model_metadata(model_name)
        if meta and meta.fallback_model:
            return meta.fallback_model
        return "qwen2.5:1.5b"

    def resolve_fallback_chain(self, primary_model: str) -> str:
        """Walks fallback chain until finding a model actually installed in local Ollama."""
        if self.is_installed(primary_model):
            return primary_model

        curr = primary_model
        visited = set()
        while curr and curr not in visited:
            visited.add(curr)
            meta = self.get_model_metadata(curr)
            if not meta or not meta.fallback_model:
                break
            fb = meta.fallback_model
            if self.is_installed(fb):
                logger.info(f"[MODEL_REGISTRY] Model '{primary_model}' missing -> selected fallback '{fb}'")
                return fb
            curr = fb

        # If chain exhausted, find any installed non-embedding model
        installed = self.get_installed_models()
        text_models = [m for m in installed if "embed" not in m]
        if text_models:
            fallback = text_models[0]
            logger.info(f"[MODEL_REGISTRY] All fallbacks exhausted for '{primary_model}' -> using '{fallback}'")
            return fallback

        return primary_model


class ModelString(str):
    """String subclass that preserves string compatibility while providing model metadata attributes."""
    def __new__(cls, val: str, meta: Optional[ModelMetadata] = None):
        obj = super().__new__(cls, val)
        obj._meta = meta
        return obj

    @property
    def capabilities(self) -> List[str]:
        if getattr(self, "_meta", None):
            return self._meta.capabilities
        from llm.model_registry import model_registry
        m = model_registry.get_model_metadata(str(self))
        return m.capabilities if m else []

    @property
    def vram_estimate_mb(self) -> int:
        if getattr(self, "_meta", None):
            return self._meta.vram_estimate_mb
        from llm.model_registry import model_registry
        m = model_registry.get_model_metadata(str(self))
        return m.vram_estimate_mb if m else 2000

    @property
    def fallback_model(self) -> Optional[str]:
        if getattr(self, "_meta", None):
            return self._meta.fallback_model
        from llm.model_registry import model_registry
        m = model_registry.get_model_metadata(str(self))
        return m.fallback_model if m else None


model_registry = ModelRegistry()