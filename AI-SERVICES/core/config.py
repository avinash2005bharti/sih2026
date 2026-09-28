from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

ENV_FILE_PATH = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    APP_NAME: str = "Sovereign AI Service"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Base and Storage Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = Path(__file__).resolve().parent.parent / "storage"
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "storage" / "uploads"
    ARTIFACT_DIR: Path = Path(__file__).resolve().parent.parent / "storage" / "artifacts"
    TEMP_DIR: Path = Path(__file__).resolve().parent.parent / "storage" / "temp"

    # Default General Model
    DEFAULT_GENERAL_MODEL: str = "qwen2.5:1.5b"

    # Hardware Profile: AUTO, GPU_RTX2050, or CPU_ONLY
    HARDWARE_PROFILE: str = "AUTO"

    # Ollama Infrastructure
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_KEEP_ALIVE: str = "5m"  # Keep-alive window for lazy VRAM lifecycle
    OLLAMA_AUTO_PULL: bool = False  # Set True to auto-pull missing models at startup


    # RTX 2050 4GB VRAM Model Stack (SIH 26117 Centralized Registry)
    GPU_CLASSIFIER_MODEL: str = "qwen3:0.6b"          # Fast classifier (522MB) ✅
    GPU_ROUTER_MODEL: str = "qwen3:0.6b"              # Intent router (522MB) ✅
    GPU_MAIN_MODEL: str = "qwen2.5:1.5b"              # General chat (986MB) ✅
    GPU_GENERAL_MODEL: str = "qwen2.5:1.5b"           # Explicit general alias
    GPU_PLANNER_MODEL: str = "qwen3:1.7b"             # Advanced planning (1.1GB) ✅
    GPU_REASONING_MODEL: str = "qwen3:1.7b"           # Advanced document & industrial reasoning (1.1GB) ✅
    GPU_FALLBACK_MODEL: str = "qwen2.5:0.5b"          # Ultra-fast fallback (397MB) ✅
    GPU_CODER_MODEL: str = "qwen2.5-coder:1.5b"       # Coding (986MB) ✅
    GPU_CODER_HEAVY_MODEL: str = "qwen2.5-coder:3b"   # Heavy coding fallback (1.9GB) ✅
    GPU_VISION_MODEL: str = "qwen2.5vl:3b"            # Primary vision (1.9GB) ✅
    GPU_VISION_FALLBACK: str = "qwen2.5vl:3b"         # Vision fallback (3.2GB) ✅
    GPU_LIGHT_VISION_MODEL: str = "qwen2.5vl:3b"      # Lightweight vision fallback
    EMBEDDING_MODEL: str = "nomic-embed-text"          # Embeddings (274MB) ✅

    # Models to keep warm in Ollama (comma-separated)
    ALWAYS_WARM_MODELS: str = "qwen2.5:0.5b,qwen2.5:1.5b,qwen3:0.6b,nomic-embed-text"

    # CPU-Only Lightweight Model Stack
    CPU_CLASSIFIER_MODEL: str = "qwen2.5:0.5b"
    CPU_MAIN_MODEL: str = "qwen2.5:1.5b"
    CPU_CODER_MODEL: str = "qwen2.5-coder:1.5b"
    CPU_VISION_MODEL: str = "qwen2.5vl:3b"

    # Backwards-compatible aliases (updated to match installed models)
    OLLAMA_CHAT_MODEL: str = "qwen2.5:1.5b"
    OLLAMA_CODE_MODEL: str = "qwen2.5-coder:1.5b"
    OLLAMA_VISION_MODEL: str = "qwen2.5vl:3b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text:latest"
    RAG_TOP_K: int = 5

    # Multimodal: Vision & OCR
    VISION_MODEL: str = "qwen2.5vl:3b"
    OCR_ENGINE: str = "pytesseract"
    OCR_USE_GPU: bool = False
    OCR_DEVICE: str = "cpu"
    OCR_PREPROCESSING_ENABLED: bool = True
    OCR_CONTRAST_ENHANCEMENT: bool = True
    OCR_SHARPEN: bool = True
    OCR_MAX_DIMENSION: int = 2048

    # Valkey Cache (Redis-protocol compatible)
    VALKEY_URL: str = "redis://localhost:6379"
    VALKEY_ENABLED: bool = True

    # Qdrant Vector Database
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "sovereign_documents"
    QDRANT_MEMORY_COLLECTION: str = "sovereign_ai_memory"
    QDRANT_VECTOR_SIZE: int = 768  # nomic-embed-text produces 768-dim vectors

    # Memory Architecture Settings
    MEMORY_ENABLED: bool = True
    STM_ENABLED: bool = True
    STM_MAX_MESSAGES: int = 20
    STM_MAX_TOKENS: int = 8000
    LTM_ENABLED: bool = True
    LTM_TOP_K: int = 5
    LTM_SCORE_THRESHOLD: float = 0.35
    LTM_MAX_CONTEXT: int = 4000
    MEM0_ENABLED: bool = True

    # Embedding Provider
    EMBEDDING_PROVIDER: str = "ollama"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_URL: str = "http://localhost:7474"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "sovereignpass"
    NEO4J_DATABASE: str = "neo4j"

    # MongoDB for STM and operations
    MONGO_URI: str = "mongodb://admin:admin@localhost:27017/sovereign_ai?authSource=admin"
    MONGO_DB_NAME: str = "sovereign_ai"

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = str(ENV_FILE_PATH)
        case_sensitive = True
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    s.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    s.ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    s.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return s

settings = get_settings()