"""
Health check endpoints for Sovereign AI Workbench.
Monitors FastAPI API status, Ollama connectivity, Moondream vision model, and local PaddleOCR engine.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from llm.ollama_client import ollama_client
from llm.model_router import model_router
from core.config import settings
from core.logging import logger
from core.hardware import detect_hardware
from ocr.ocr_service import ocr_service

router = APIRouter()


class ServiceStatus(BaseModel):
    """Service status information."""
    name: str
    status: str
    detail: Optional[str] = None


class OllamaHealthInfo(BaseModel):
    available: bool
    url: str
    modelsAvailable: bool
    count: Optional[int] = 0


class HardwareHealthInfo(BaseModel):
    nvidiaAvailable: bool
    mode: str
    gpuName: Optional[str] = None
    driverVersion: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    app_name: str
    status: str
    api: str = "ok"
    ollama: str = "ok"
    vision_model: str = "moondream"
    ocr: str = "ok"
    ocr_engine: Optional[str] = "paddleocr"
    services: Dict[str, ServiceStatus]
    ollama_details: OllamaHealthInfo
    hardware: HardwareHealthInfo
    available_models: List[str]
    configured_models: Dict[str, str]


@router.get("/health", response_model=HealthResponse, summary="Health check")
@router.get("/api/health", response_model=HealthResponse, summary="Compatibility health check")
async def health():
    """
    Check health of AI Service, local Ollama connectivity, dedicated OCR engine, and hardware mode.
    Never crashes if Ollama, OCR, or GPU is unavailable.
    """
    logger.info("Health check requested")

    # 1. Safe hardware detection
    hw = detect_hardware()
    hardware_info = HardwareHealthInfo(
        nvidiaAvailable=hw.get("nvidiaAvailable", False),
        mode=hw.get("mode", "cpu"),
        gpuName=hw.get("gpuName"),
        driverVersion=hw.get("driverVersion")
    )

    # 2. Safe Ollama probe
    ollama_check = await ollama_client.health_check()
    is_ollama_available = ollama_check.get("available", False)
    models_available = ollama_check.get("models_available", [])
    has_models = len(models_available) > 0

    ollama_info = OllamaHealthInfo(
        available=is_ollama_available,
        url=settings.OLLAMA_BASE_URL,
        modelsAvailable=has_models,
        count=len(models_available)
    )

    ollama_status_str = "ok" if is_ollama_available else "unavailable"

    # 3. Dedicated OCR Status Probe
    ocr_status_dict = ocr_service.get_status()
    ocr_is_ok = ocr_status_dict.get("status") == "ok"
    ocr_status_str = "ok" if ocr_is_ok else "unavailable"
    ocr_engine_name = ocr_status_dict.get("engine", "paddleocr")

    # 4. Vision Model
    vision_model_name = getattr(settings, "VISION_MODEL", "moondream")

    # 5. Memory Architecture Status Probe
    try:
        from memory import memory_manager
        mem_health = await memory_manager.health_check()
        mem_status_str = mem_health.get("memory", "unknown")
    except Exception as e:
        mem_status_str = "unavailable"

    # Status services map
    services_map = {
        "fastapi": ServiceStatus(name="FastAPI", status="running"),
        "ollama": ServiceStatus(
            name="Ollama",
            status="connected" if is_ollama_available else "disconnected",
            detail=ollama_check.get("detail")
        ),
        "ocr": ServiceStatus(
            name="PaddleOCR",
            status="ready" if ocr_is_ok else "unavailable",
            detail=ocr_status_dict.get("error")
        ),
        "memory": ServiceStatus(
            name="LocalMemory",
            status="ready" if mem_status_str == "healthy" else mem_status_str
        )
    }

    # Status is healthy if FastAPI, Ollama, OCR, and Memory are up; degraded if partial
    overall_status = "healthy" if (is_ollama_available and ocr_is_ok) else "degraded"
    configured_models = model_router.get_all_models()

    logger.info(
        f"Health check complete | status={overall_status} | "
        f"ollama={ollama_status_str} | vision={vision_model_name} | ocr={ocr_status_str} ({ocr_engine_name})"
    )

    return HealthResponse(
        app_name=settings.APP_NAME,
        status=overall_status,
        api="ok",
        ollama=ollama_status_str,
        vision_model=vision_model_name,
        ocr=ocr_status_str,
        ocr_engine=ocr_engine_name if ocr_is_ok else None,
        services=services_map,
        ollama_details=ollama_info,
        hardware=hardware_info,
        available_models=models_available,
        configured_models=configured_models
    )


@router.get("/health/models", summary="Inspect detailed model status")
@router.get("/api/health/models", summary="Inspect detailed model status")
async def health_models():
    """
    Expose health, size, and availability of all sovereign models, including OCR and Vision.
    """
    try:
        ollama_health = await ollama_client.health_check()
        available_names = ollama_health.get("models_available", [])
        configured = model_router.get_all_models()

        models_status = {}
        for role, model_name in configured.items():
            is_present = any(model_name in name or name.startswith(model_name.split(":")[0]) for name in available_names)
            models_status[role] = {
                "model": model_name,
                "available": is_present,
                "status": "ready" if is_present else "missing"
            }

        # Include OCR engine in model status
        ocr_info = ocr_service.get_status()
        models_status["ocr"] = {
            "model": ocr_info.get("engine", "paddleocr"),
            "available": ocr_info.get("status") == "ok",
            "status": "ready" if ocr_info.get("status") == "ok" else "unavailable"
        }

        return {
            "status": "ok" if all(m["available"] for m in models_status.values() if m["model"]) else "degraded",
            "installed_models": available_names,
            "roles": models_status
        }
    except Exception as e:
        logger.error(f"Models health check error: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/health/memory", summary="Memory system health")
@router.get("/api/health/memory", summary="Memory system health (compatibility)")
async def health_memory():
    """Check health of all memory subsystems: STM, LTM, Qdrant, Neo4j, Mem0, Embeddings."""
    try:
        from memory import memory_manager
        status = await memory_manager.health_check()
        return status
    except Exception as e:
        logger.error(f"Memory health check error: {e}")
        return {"memory": "unavailable", "error": str(e)}


@router.get("/health/ai", summary="Comprehensive Sovereign AI Enclave Health Check")
@router.get("/api/health/ai", summary="Comprehensive Sovereign AI Enclave Health Check (compatibility)")
async def health_ai():
    """
    Checks all five local enclave services and SLM specialist models:
    - Ollama (Local SLMs)
    - Qdrant (Vector Database)
    - Neo4j (Knowledge Graph)
    - MongoDB (Operational & Document Storage)
    - Valkey (High-Speed Memory & Cache)
    - Specialist Models (Router, Planner, Coding, Vision, Embedding, Document, Risk, Compliance, Critic)
    """
    import socket
    import pymongo
    from rag.qdrant_client import qdrant_client
    from llm.model_registry import model_registry

    # 1. Ollama Check
    ollama_health = await ollama_client.health_check()
    ollama_ok = bool(ollama_health.get("available", False))
    available_models = set(ollama_health.get("models_available", []))

    # 2. Qdrant Check
    try:
        qdrant_ok = await qdrant_client.health_check()
    except Exception:
        qdrant_ok = False

    # 3. Neo4j Check
    neo4j_ok = False
    try:
        from memory.graph.neo4j_service import neo4j_service
        drv = neo4j_service._get_driver()
        if drv is not None:
            neo4j_ok = True
        else:
            # Socket test fallback
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            s.connect(("localhost", 7687))
            s.close()
            neo4j_ok = True
    except Exception:
        neo4j_ok = False

    # 4. MongoDB Check
    mongodb_ok = False
    try:
        client = pymongo.MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=1500, connectTimeoutMS=1500)
        client.admin.command("ping")
        mongodb_ok = True
    except Exception:
        try:
            # Try 127.0.0.1 fallback
            client = pymongo.MongoClient("mongodb://admin:admin@127.0.0.1:27017/sovereign_ai?authSource=admin", serverSelectionTimeoutMS=1500)
            client.admin.command("ping")
            mongodb_ok = True
        except Exception:
            mongodb_ok = False

    # 5. Valkey Check
    valkey_ok = False
    for host in ["127.0.0.1", "localhost"]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            s.connect((host, 6379))
            s.sendall(b"PING\r\n")
            resp = s.recv(128)
            s.close()
            if b"+PONG" in resp:
                valkey_ok = True
                break
        except Exception:
            pass

    # 6. SLM Models Availability Check
    def _is_model_available(role: str) -> bool:
        active_model = model_registry.get_model(role)
        base = active_model.split(":")[0]
        return any(active_model in m or m.startswith(base) for m in available_models)

    models_status = {
        "router": _is_model_available("router"),
        "planner": _is_model_available("planner"),
        "coding": _is_model_available("coding"),
        "vision": _is_model_available("vision"),
        "embedding": _is_model_available("embedding"),
        "document": _is_model_available("document"),
        "risk": _is_model_available("risk"),
        "compliance": _is_model_available("compliance"),
        "critic": _is_model_available("critic"),
    }

    return {
        "ollama": ollama_ok,
        "qdrant": qdrant_ok,
        "neo4j": neo4j_ok,
        "mongodb": mongodb_ok,
        "valkey": valkey_ok,
        "models": models_status
    }

