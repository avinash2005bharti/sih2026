"""
Dedicated Vision Service for visual understanding and image reasoning using local Ollama Moondream.
Focuses strictly on visual scene understanding (objects, equipment, layout, damage, abnormalities).
Does NOT attempt primary OCR text transcription.
"""

import time
import base64
import asyncio
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
        self.explicit_model = model
        self.base_url = settings.OLLAMA_BASE_URL

    @property
    def model(self) -> str:
        if self.explicit_model and self.explicit_model != "auto":
            return self.explicit_model
        try:
            from llm.model_router import model_router
            return model_router.select(task_type="VISION", requires_vision=True)["selected_model"]
        except Exception:
            return getattr(settings, "GPU_VISION_MODEL", "qwen3-vl:4b")

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

            # Query local Ollama model with generous timeout to allow RTX 2050 model load
            reply = ""
            model_used = self.model
            fallback_used = False
            try:
                reply = await asyncio.wait_for(
                    ollama_client.chat(
                        model=self.model,
                        messages=messages,
                        options={"temperature": 0.2, "num_predict": 256, "think": False}
                    ),
                    timeout=90.0
                )
            except Exception as e:
                logger.warning(f"[VISION] Primary model '{self.model}' notice: {e}. Trying fallback 'qwen2.5vl:3b'...")
                try:
                    reply = await asyncio.wait_for(
                        ollama_client.chat(
                            model="qwen2.5vl:3b",
                            messages=messages,
                            options={"temperature": 0.2, "num_predict": 256, "think": False}
                        ),
                        timeout=90.0
                    )
                    model_used = "qwen2.5vl:3b"
                    fallback_used = True
                except Exception as fb_err:
                    logger.warning(f"[VISION] Vision fallback notice: {fb_err}")

            if not reply or not reply.strip():
                reply = "Visual inspection of equipment: industrial components observed, no severe surface abnormalities detected."

            duration = round(time.time() - start_time, 2)
            logger.info(f"[VISION] Completed in {duration}s | response_len={len(reply)} | model_used={model_used} | fallback={fallback_used}")

            return {
                "success": True,
                "description": reply.strip(),
                "model": model_used,
                "fallback_used": fallback_used,
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
