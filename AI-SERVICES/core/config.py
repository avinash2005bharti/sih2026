from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

ENV_FILE_PATH = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    APP_NAME: str = "Sovereign AI Service"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "qwen2.5:1.5b"
    OLLAMA_CODE_MODEL: str = "qwen2.5-coder:1.5b"
    OLLAMA_VISION_MODEL: str = "moondream:latest"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text:latest"

    # Multimodal: Vision & OCR
    VISION_MODEL: str = "moondream:latest"
    OCR_ENGINE: str = "paddleocr"
    OCR_USE_GPU: bool = False
    OCR_DEVICE: str = "cpu"
    OCR_PREPROCESSING_ENABLED: bool = True
    OCR_CONTRAST_ENHANCEMENT: bool = True
    OCR_SHARPEN: bool = True
    OCR_MAX_DIMENSION: int = 2048

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

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()