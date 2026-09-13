"""
API routes for model information, discovery, and role management.
Discovers models directly from local Ollama installation (http://localhost:11434).
"""

import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from llm.model_router import model_router
from llm.ollama_client import ollama_client
from core.logging import logger
from core.config import settings

router = APIRouter(prefix="/api")


class ModelInfo(BaseModel):
    """Detailed model information."""
    name: str
    type: str
    capabilities: List[str]
    description: str
    available: bool = True
    size: Optional[str] = None
    provider: Optional[str] = "ollama"
    local: Optional[bool] = True


class ModelsResponse(BaseModel):
    """Response with list of available models."""
    models: List[ModelInfo]
    default_model: str


class ModelRoleUpdate(BaseModel):
    """Request to assign a model to a role."""
    role: str = Field(..., description="Role name: chat, coding, vision, or embedding")
    model: str = Field(..., description="Model name installed in local Ollama")


class PullModelRequest(BaseModel):
    model: str


@router.get("/models", response_model=ModelsResponse, summary="List available models")
async def get_models():
    """
    Get information about all installed models in local Ollama, plus dedicated local engines like PaddleOCR.
    """
    try:
        from ocr.ocr_service import ocr_service

        logger.info("Fetching installed models from local Ollama and local OCR engine")
        detailed_models = await ollama_client.list_models_detailed()

        models = []
        for m in detailed_models:
            m_name = m["name"]
            is_vision = "moondream" in m_name.lower() or "vl" in m_name.lower() or "vision" in m_name.lower()
            models.append(
                ModelInfo(
                    name=m_name,
                    type="vision" if is_vision else m.get("type", "llm").lower(),
                    capabilities=["vision", "scene_understanding"] if is_vision else m.get("capabilities", ["text_generation"]),
                    description=f"{m.get('family', 'Ollama')} model ({m.get('parameterSize', 'unknown parameters')})",
                    available=True,
                    size=m.get("size"),
                    provider="ollama",
                    local=True
                )
            )

        # Append dedicated local OCR engine
        ocr_status = ocr_service.get_status()
        models.append(
            ModelInfo(
                name="paddleocr",
                type="ocr",
                capabilities=["ocr", "text_extraction", "exact_reading"],
                description="Dedicated local Optical Character Recognition engine (PaddleOCR)",
                available=ocr_status.get("status") == "ok",
                size="45MB",
                provider="local",
                local=True
            )
        )

        # If local Ollama has no models yet, list configured default models as unavailable
        if not models:
            for role, name in model_router.get_roles().items():
                models.append(
                    ModelInfo(
                        name=name,
                        type="Vision" if "vl" in name or "vision" in name else "LLM",
                        capabilities=["text_generation"],
                        description=f"Default {role} model (not yet installed)",
                        available=False,
                        size="Not installed"
                    )
                )

        current_roles = model_router.get_roles()
        default_model = current_roles.get("chat", settings.OLLAMA_CHAT_MODEL)

        return ModelsResponse(
            models=models,
            default_model=default_model
        )

    except Exception as e:
        logger.error(f"Error fetching models from Ollama: {e}")
        # Never crash the endpoint; return fallback
        current_roles = model_router.get_roles()
        return ModelsResponse(
            models=[],
            default_model=current_roles.get("chat", settings.OLLAMA_CHAT_MODEL)
        )


@router.get("/models/ollama", summary="List installed Ollama models")
async def get_ollama_models():
    """Get raw list of installed models from local Ollama tags API."""
    try:
        detailed = await ollama_client.list_models_detailed()
        return {"success": True, "models": detailed, "count": len(detailed)}
    except Exception as e:
        logger.error(f"Error in get_ollama_models: {e}")
        return {"success": False, "models": [], "error": str(e)}


@router.get("/models/roles", summary="Get model role configurations")
async def get_model_roles():
    """Get active model assignments for Chat, Coding, Vision, and Embedding roles."""
    return {
        "success": True,
        "roles": model_router.get_roles()
    }


@router.put("/models/roles", summary="Update a model role assignment")
async def update_model_role(payload: ModelRoleUpdate):
    """
    Configure which installed local Ollama model is used for each role.
    Allowed roles: 'chat', 'coding', 'vision', 'embedding'.
    """
    valid_roles = ["chat", "coding", "vision", "embedding"]
    if payload.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{payload.role}'. Must be one of: {valid_roles}"
        )

    model_router.set_role(payload.role, payload.model)
    return {
        "success": True,
        "message": f"Role '{payload.role}' assigned to model '{payload.model}'",
        "roles": model_router.get_roles()
    }


@router.post("/models/pull", summary="Pull a model from Ollama")
async def pull_model(request: PullModelRequest):
    """Pull/download a model into the local Ollama instance upon explicit user/admin request."""
    model_name = request.model.strip()
    if not model_name:
        raise HTTPException(status_code=400, detail="Model name is required")

    if not re.match(r'^[a-zA-Z0-9._:/-]+$', model_name):
        raise HTTPException(status_code=400, detail="Invalid model name characters")

    try:
        logger.info(f"Starting explicit model pull: {model_name}")
        result = await ollama_client.pull_model(model_name)
        logger.info(f"Model pull completed: {model_name}")
        return {
            "success": True,
            "message": f"Model '{model_name}' pulled successfully",
            "model": model_name,
            "status": result.get("status", "success")
        }
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Model pull error: {e}")
        raise HTTPException(status_code=502, detail=f"Model pull failed: {str(e)}")


@router.get("/models/{model_name}", response_model=ModelInfo, summary="Get model details")
async def get_model_details(model_name: str):
    """Get details for a specific model."""
    try:
        detailed = await ollama_client.list_models_detailed()
        for m in detailed:
            if m["name"] == model_name or m["name"].split(":")[0] == model_name.split(":")[0]:
                return ModelInfo(
                    name=m["name"],
                    type=m.get("type", "LLM"),
                    capabilities=m.get("capabilities", ["text_generation"]),
                    description=f"{m.get('family', 'Ollama')} model",
                    available=True,
                    size=m.get("size")
                )

        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found in local Ollama installation"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching model details: {e}")
        raise HTTPException(status_code=502, detail=str(e))
