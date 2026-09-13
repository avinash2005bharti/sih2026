from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Sovereign AI Service"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "qwen2.5-coder:3b"
    OLLAMA_CODE_MODEL: str = "qwen2.5-coder:3b"
    OLLAMA_VISION_MODEL: str = "moondream"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text:latest"

    # Multimodal: Vision & OCR
    VISION_MODEL: str = "moondream"
    OCR_ENGINE: str = "paddleocr"
    OCR_USE_GPU: bool = False
    OCR_DEVICE: str = "cpu"
    OCR_PREPROCESSING_ENABLED: bool = True
    OCR_CONTRAST_ENHANCEMENT: bool = True
    OCR_SHARPEN: bool = True
    OCR_MAX_DIMENSION: int = 2048

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "sovereign_documents"
    QDRANT_VECTOR_SIZE: int = 768  # nomic-embed-text produces 768-dim vectors

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()