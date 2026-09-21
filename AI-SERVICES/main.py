from contextlib import asynccontextmanager
from pathlib import Path
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.openapi.utils import get_openapi
import urllib.parse

from core.config import settings
from core.logging import logger
from core.hardware import detect_hardware
from llm.ollama_client import ollama_client
from api.routes import health, chat, models, documents, vision, tasks, memory_routes, network


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
app.include_router(documents.router, tags=["documents"])
app.include_router(vision.router, tags=["vision"])
app.include_router(tasks.router, tags=["tasks"])
app.include_router(memory_routes.router, prefix="/api/memory", tags=["memory"])
app.include_router(network.router, tags=["network"])

# Workspace files & generated sovereign artifacts endpoint
workspace_dir = (Path(__file__).parent / "workspace").resolve()
workspace_dir.mkdir(parents=True, exist_ok=True)
reports_dir = (workspace_dir / "reports").resolve()
reports_dir.mkdir(parents=True, exist_ok=True)


@app.api_route("/workspace/{file_path:path}", methods=["GET", "HEAD"], summary="Serve workspace artifacts and reports")
async def serve_workspace_file(file_path: str):
    """
    Serve generated reports, PDFs, Excel sheets, and documents from workspace or uploads.
    Handles relative paths ('reports/abc.pdf'), filenames ('abc.pdf'),
    or URL-encoded absolute paths ('C%3A/Users/.../workspace/reports/abc.pdf').
    """
    try:
        raw = urllib.parse.unquote(file_path).strip().replace("\\", "/")

        candidates = []

        # 1. Direct absolute path check (e.g. if C:/... was URL-encoded)
        direct_p = Path(raw)
        if direct_p.is_absolute() and direct_p.exists() and direct_p.is_file():
            candidates.append(direct_p)

        # 2. Path relative to workspace_dir
        cleaned = raw
        if "workspace/" in cleaned:
            cleaned = cleaned.split("workspace/", 1)[-1]
        elif "reports/" in cleaned:
            cleaned = "reports/" + cleaned.split("reports/", 1)[-1]

        ws_candidate = (workspace_dir / cleaned.lstrip("/")).resolve()
        if ws_candidate.exists() and ws_candidate.is_file():
            candidates.append(ws_candidate)

        # 3. Check inside workspace_dir / reports
        filename_only = Path(raw).name
        rep_candidate = (workspace_dir / "reports" / filename_only).resolve()
        if rep_candidate.exists() and rep_candidate.is_file():
            candidates.append(rep_candidate)

        # 4. Check in BACKEND uploads
        uploads_doc = (Path(__file__).parent.parent / "BACKEND" / "uploads" / "documents" / filename_only).resolve()
        if uploads_doc.exists() and uploads_doc.is_file():
            candidates.append(uploads_doc)

        # 5. Check direct workspace root
        ws_root_candidate = (workspace_dir / filename_only).resolve()
        if ws_root_candidate.exists() and ws_root_candidate.is_file():
            candidates.append(ws_root_candidate)

        for target in candidates:
            if target.exists() and target.is_file():
                ext = target.suffix.lower()
                media_type = "application/octet-stream"
                if ext == ".pdf":
                    media_type = "application/pdf"
                elif ext == ".xlsx":
                    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif ext == ".docx":
                    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif ext == ".csv":
                    media_type = "text/csv; charset=utf-8"
                elif ext in [".txt", ".md"]:
                    media_type = "text/plain; charset=utf-8"
                elif ext == ".json":
                    media_type = "application/json"
                elif ext == ".svg":
                    media_type = "image/svg+xml"
                elif ext == ".png":
                    media_type = "image/png"
                elif ext in [".jpg", ".jpeg"]:
                    media_type = "image/jpeg"

                return FileResponse(
                    path=str(target),
                    filename=target.name,
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"inline; filename=\"{target.name}\"",
                        "Access-Control-Allow-Origin": "*",
                    }
                )

        logger.warning(f"[WORKSPACE_SERVE] File not found: raw='{raw}', searched: {[str(c) for c in candidates]}")
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_SERVE] Error serving file '{file_path}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
