"""
Lightweight and configurable image preprocessing pipeline for dedicated OCR.
Designed for CPU-friendly execution and low-memory (8GB RAM) footprints.
"""

import io
import base64
import gc
from pathlib import Path
from typing import Union, Tuple, Optional
import numpy as np
from PIL import Image, ImageOps, ImageEnhance

from core.config import settings
from core.logging import logger


class ImagePreprocessor:
    """Preprocesses images for optimal OCR text recognition without damaging image content."""

    def __init__(
        self,
        enabled: Optional[bool] = None,
        contrast_enhancement: Optional[bool] = None,
        sharpen: Optional[bool] = None,
        max_dimension: Optional[int] = None,
    ):
        self.enabled = enabled if enabled is not None else settings.OCR_PREPROCESSING_ENABLED
        self.contrast_enhancement = (
            contrast_enhancement
            if contrast_enhancement is not None
            else settings.OCR_CONTRAST_ENHANCEMENT
        )
        self.sharpen = sharpen if sharpen is not None else settings.OCR_SHARPEN
        self.max_dimension = max_dimension or settings.OCR_MAX_DIMENSION

    def load_image(self, image_source: Union[str, bytes, Image.Image]) -> Image.Image:
        """
        Load an image from various sources (file path, base64 string, raw bytes, or PIL Image).
        Converts to standard RGB.
        """
        if isinstance(image_source, Image.Image):
            img = image_source.convert("RGB")
            return img

        if isinstance(image_source, bytes):
            img = Image.open(io.BytesIO(image_source))
            return img.convert("RGB")

        if isinstance(image_source, str):
            # Check if base64 data URI or raw base64
            if image_source.startswith("data:image"):
                base64_data = image_source.split(",", 1)[1]
                image_bytes = base64.b64decode(base64_data)
                img = Image.open(io.BytesIO(image_bytes))
                return img.convert("RGB")
            
            # Check if file path
            path = Path(image_source)
            if path.exists() and path.is_file():
                img = Image.open(str(path))
                return img.convert("RGB")

            # Check if raw base64 string
            try:
                image_bytes = base64.b64decode(image_source)
                img = Image.open(io.BytesIO(image_bytes))
                return img.convert("RGB")
            except Exception:
                raise ValueError("Unsupported image source: not a valid file path, data URI, or base64 string.")

        raise TypeError(f"Unsupported image_source type: {type(image_source)}")

    def preprocess(self, image_source: Union[str, bytes, Image.Image]) -> Tuple[np.ndarray, Image.Image]:
        """
        Run safe, lightweight preprocessing on image.

        Returns:
            Tuple of (numpy_array_for_ocr, processed_pil_image)
        """
        img = self.load_image(image_source)

        if not self.enabled:
            np_img = np.array(img)
            return np_img, img

        # 1. Orientation handling (EXIF rotation)
        try:
            img = ImageOps.exif_transpose(img) or img
        except Exception as e:
            logger.debug(f"[OCR-PREPROCESS] EXIF transpose skipped: {e}")

        # 2. Resize if dimension exceeds max_dimension to protect 8GB RAM
        width, height = img.size
        if max(width, height) > self.max_dimension:
            scale = self.max_dimension / float(max(width, height))
            new_w = max(1, int(width * scale))
            new_h = max(1, int(height * scale))
            logger.info(f"[OCR-PREPROCESS] Resizing image from {width}x{height} to {new_w}x{new_h} to conserve memory")
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 3. Contrast enhancement if enabled
        if self.contrast_enhancement:
            try:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.25)
            except Exception as e:
                logger.debug(f"[OCR-PREPROCESS] Contrast enhancement skipped: {e}")

        # 4. Sharpening if enabled
        if self.sharpen:
            try:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.3)
            except Exception as e:
                logger.debug(f"[OCR-PREPROCESS] Sharpening skipped: {e}")

        np_img = np.array(img)

        # Explicit garbage collection for intermediate allocations
        gc.collect()

        return np_img, img


# Global singleton instance
image_preprocessor = ImagePreprocessor()
