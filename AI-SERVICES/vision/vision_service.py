"""
Dedicated Vision Service for visual understanding and image reasoning using local Ollama Moondream.
Focuses strictly on visual scene understanding (objects, equipment, layout, damage, abnormalities).
Does NOT attempt primary OCR text transcription.
"""

import time
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Union
from PIL import Image
import io

from llm.ollama_client import ollama_client
from core.config import settings
from core.logging import logger

# Specialized system/prompt instruction preventing Moondream from hallucinating text transcription
DEFAULT_VISION_ANALYSIS_PROMPT = (
    "Describe the visual contents of this image.\n"
    "Do not attempt to transcribe text.\n"
    "Focus on objects, equipment, layout, damage, abnormalities, "
    "symbols and visual relationships."
)


class VisionService:
    """Dedicated visual understanding service powered by local Moondream via Ollama."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or getattr(settings, "VISION_MODEL", "moondream")
        self.base_url = settings.OLLAMA_BASE_URL
        logger.info(f"[VISION] Initialized VisionService with model='{self.model}' at {self.base_url}")

    def _prepare_image_base64(self, image_source: Union[str, bytes, Image.Image]) -> str:
        """Convert any valid image source into clean base64 string for Ollama."""
        if isinstance(image_source, Image.Image):
            buffer = io.BytesIO()
            image_source.save(buffer, format="JPEG", quality=90)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

        if isinstance(image_source, bytes):
            return base64.b64encode(image_source).decode("utf-8")

        if isinstance(image_source, str):
            # If already data URI
            if image_source.startswith("data:image"):
                return image_source.split(",", 1)[1]

            # If local file path
            path = Path(image_source)
            if path.exists() and path.is_file():
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")

            # Assume already base64 string
            return image_source

        raise TypeError(f"Unsupported image_source type for vision: {type(image_source)}")

    async def analyze_visual_scene(
        self,
        image_source: Union[str, bytes, Image.Image],
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze visual features, equipment condition, scene layout, and physical abnormalities.

        Args:
            image_source: Base64 image, bytes, file path, or PIL Image.
            prompt: Optional specific question about visual features. Defaults to visual reasoning prompt.

        Returns:
            Dict containing success flag, visual description, duration, and model used.
        """
        start_time = time.time()
        logger.info(f"[VISION] Sending image to {self.model}")

        try:
            image_base64 = self._prepare_image_base64(image_source)
            effective_prompt = prompt.strip() if (prompt and prompt.strip()) else DEFAULT_VISION_ANALYSIS_PROMPT

            messages = [
                {
                    "role": "user",
                    "content": effective_prompt,
                    "images": [image_base64]
                }
            ]

            # Query local Ollama model
            reply = await ollama_client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.2, "num_predict": 512}
            )

            duration = round(time.time() - start_time, 2)
            logger.info(f"[VISION] Completed in {duration}s | response_len={len(reply)}")

            return {
                "success": True,
                "description": reply.strip(),
                "model": self.model,
                "duration_seconds": duration
            }

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            logger.error(f"[VISION] Moondream vision analysis failed after {duration}s: {e}", exc_info=True)
            return {
                "success": False,
                "description": "Visual analysis unavailable due to model or connection error.",
                "error": str(e),
                "model": self.model,
                "duration_seconds": duration
            }

    async def is_model_ready(self) -> bool:
        """Check whether the configured vision model is available in Ollama."""
        try:
            health = await ollama_client.health_check()
            if not health.get("available"):
                return False
            available_models = health.get("models_available", [])
            return any(
                self.model == m or m.startswith(f"{self.model}:")
                for m in available_models
            )
        except Exception:
            return False

    # Alias for convenience
    describe_scene = analyze_visual_scene


# Global singleton instance
vision_service = VisionService()
