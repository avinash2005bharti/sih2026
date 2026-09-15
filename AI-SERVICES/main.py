from contextlib import asynccontextmanager
from pathlib import Path
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

from core.config import settings
from core.logging import logger
from core.hardware import detect_hardware
from llm.ollama_client import ollama_client
from api.routes import health, chat, models, documents, vision, tasks, memory_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup checks and shutdown cleanup."""
    logger.info(f"{'='*60}")
    logger.info(f"{settings.APP_NAME} starting up")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"Ollama Endpoint: {settings.OLLAMA_BASE_URL}")

    # Safe hardware detection
    hw = detect_hardware()
    if hw.get("nvidiaAvailable"):
        logger.info(f"Hardware: NVIDIA GPU detected -> {hw.get('gpuName')} (Driver: {hw.get('driverVersion')})")
        logger.info("GPU acceleration mode enabled for local Ollama")
    else:
        logger.info("Hardware: NVIDIA GPU not available -> CPU / integrated graphics mode enabled")

    # Safe Ollama reachability probe
    try:
        ollama_status = await ollama_client.health_check()
        if ollama_status.get("available"):
            models_list = ollama_status.get("models_available", [])
            logger.info(f"[OLLAMA] Connected at {settings.OLLAMA_BASE_URL} ({len(models_list)} models available)")
        else:
            logger.warning("=" * 60)
            logger.warning("[WARNING] Ollama is not installed or is not running at %s.", settings.OLLAMA_BASE_URL)
            logger.warning("Please install Ollama and run:")
            logger.warning("    ollama serve")
            logger.warning("The AI Service will continue running in offline/degraded mode.")
            logger.warning("=" * 60)
    except Exception as e:
        logger.warning(f"Ollama probe failed: {e}. Continuing in degraded mode.")

    logger.info(f"Log Level: {settings.LOG_LEVEL}")

    # Initialize Memory Architecture in background so Uvicorn binds port immediately
    async def _probe_memory():
        try:
            from memory.memory_manager import memory_manager
            mem_health = await memory_manager.health_check()
            logger.info(
                f"[MEMORY] Memory Architecture: {mem_health.get('memory')} "
                f"(STM: {mem_health.get('stm')}, LTM: {mem_health.get('ltm')}, "
                f"Qdrant: {mem_health.get('qdrant')}, Neo4j: {mem_health.get('neo4j')}, "
                f"Mem0: {mem_health.get('mem0')}, Embeddings: {mem_health.get('embedding_model')})"
            )
        except Exception as mem_err:
            logger.warning(f"Memory architecture startup warning: {mem_err}")

    asyncio.create_task(_probe_memory())
    logger.info(f"{'='*60}")

    yield

    logger.info(f"{settings.APP_NAME} shutting down")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description="Sovereign On-Premise AI Services - FastAPI Backend",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware for local development and frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React default port (old)
        "http://localhost:5173",      # Vite default port
        "http://localhost:5000",      # Node.js backend
        "http://127.0.0.1:5173",      # Local 127.0.0.1
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with proper prefixes
app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(vision.router, tags=["vision"])
app.include_router(tasks.router, tags=["tasks"])
app.include_router(memory_routes.router, prefix="/api/memory", tags=["memory"])

# Mount workspace for generated files (PDFs, reports, artifacts)
workspace_dir = (Path(__file__).parent / "workspace").resolve()
workspace_dir.mkdir(parents=True, exist_ok=True)
app.mount("/workspace", StaticFiles(directory=str(workspace_dir)), name="workspace")


# Root endpoint
@app.get("/", summary="API Info")
async def root():
    """Root endpoint - provides API information."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
