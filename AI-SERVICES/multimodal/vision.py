"""
Vision/multimodal service using Ollama vision model.
Analyzes images and visual content.
"""

import base64
from typing import Optional, List
from pathlib import Path
from llm.ollama_client import ollama_client
from core.config import settings
from core.logging import logger


class VisionService:
    """Analyze images using Ollama vision model."""

    def __init__(self, model: str = None):
        """Initialize vision service."""
        self.model = model or settings.OLLAMA_VISION_MODEL
        logger.info(f"Initialized vision service with model: {self.model}")

    async def analyze_image(self, image_source: str, prompt: str) -> str:
        """
        Analyze an image with a text prompt.

        Args:
            image_source: Base64-encoded image data or file path
            prompt: Text prompt/question about the image

        Returns:
            Analysis result from the model
        """
        try:
            # Prepare image data
            if image_source.startswith("data:image"):
                # Already base64 with data URI
                image_base64 = image_source.split(",")[1]
            elif image_source.startswith("/") or "\\" in image_source:
                # File path - read and encode
                image_base64 = await self._load_and_encode_image(image_source)
            else:
                # Assume it's already base64-encoded
                image_base64 = image_source

            # Build prompt with image
            full_prompt = f"{prompt}\n\n[Image provided for analysis]"

            # Call Ollama with vision model
            messages = [
                {
                    "role": "user",
                    "content": full_prompt,
                    "images": [image_base64]
                }
            ]

            logger.info(f"Analyzing image with prompt: {prompt[:100]}...")

            # Use Ollama chat with images
            reply = await ollama_client.chat(model=self.model, messages=messages)

            logger.debug(f"Image analysis complete | response_len={len(reply)}")
            return reply

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise

    async def extract_text_from_image(self, image_source: str) -> str:
        """
        Extract text from an image using dedicated OCR (PaddleOCR).

        Args:
            image_source: Base64-encoded image or file path

        Returns:
            Extracted text
        """
        try:
            from ocr.ocr_service import ocr_service
            result = ocr_service.extract_text(image_source)
            logger.info("Text extraction from image complete via dedicated OCR")
            return result.get("text", "")
        except Exception as e:
            logger.error(f"Dedicated OCR text extraction failed: {e}")
            raise

    async def classify_image(self, image_source: str, categories: Optional[List[str]] = None) -> dict:
        """
        Classify an image into categories.

        Args:
            image_source: Base64-encoded image or file path
            categories: Optional list of categories to classify into

        Returns:
            Classification result with category and confidence
        """
        try:
            if categories:
                category_str = ", ".join(categories)
                prompt = f"Classify this image into one of these categories: {category_str}. Explain your classification."
            else:
                prompt = "What is the main subject/category of this image? Describe it."

            result = await self.analyze_image(image_source, prompt)

            logger.info("Image classification complete")
            return {
                "classification": result,
                "model": self.model
            }

        except Exception as e:
            logger.error(f"Image classification failed: {e}")
            raise

    async def analyze_diagram(self, image_source: str) -> str:
        """
        Analyze a technical diagram or chart.

        Args:
            image_source: Base64-encoded image or file path

        Returns:
            Diagram analysis
        """
        prompt = """Analyze this diagram/chart in detail:
1. What is the main purpose/subject?
2. What are the key components or elements?
3. What relationships or connections are shown?
4. What conclusions can be drawn?

Provide a structured analysis."""

        try:
            result = await self.analyze_image(image_source, prompt)
            logger.info("Diagram analysis complete")
            return result
        except Exception as e:
            logger.error(f"Diagram analysis failed: {e}")
            raise

    @staticmethod
    async def _load_and_encode_image(file_path: str) -> str:
        """
        Load image from file and encode to base64.

        Args:
            file_path: Path to image file

        Returns:
            Base64-encoded image data
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {file_path}")

            # Support common image formats
            allowed_formats = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            if path.suffix.lower() not in allowed_formats:
                raise ValueError(f"Unsupported image format: {path.suffix}")

            # Read and encode
            with open(path, "rb") as f:
                image_data = f.read()

            image_base64 = base64.b64encode(image_data).decode("utf-8")
            logger.debug(f"Encoded image from file: {file_path}")
            return image_base64

        except Exception as e:
            logger.error(f"Error loading image: {e}")
            raise


# Global vision service instance
vision_service = VisionService()
