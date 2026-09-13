"""
OCR package providing dedicated on-premise Optical Character Recognition.
"""

from ocr.ocr_service import ocr_service, OCRService
from ocr.preprocessing import image_preprocessor, ImagePreprocessor

__all__ = ["ocr_service", "OCRService", "image_preprocessor", "ImagePreprocessor"]
