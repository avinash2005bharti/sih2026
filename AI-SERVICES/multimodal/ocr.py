"""
Industrial Optical Character Recognition (OCR) using Sovereign VLM.
Extracts structured text from nameplates, labels, schematics, and serial stamps.
"""

from typing import Any, Dict, List, Optional
from ocr.ocr_service import ocr_service
from multimodal.vision import vision_service
from core.config import settings
from core.logging import logger


class IndustrialOCR:
    """Specialized OCR engine powered by dedicated local PaddleOCR."""

    def __init__(self, model: Optional[str] = None):
        self.model = "paddleocr"
        logger.info(f"IndustrialOCR initialized with engine: {self.model}")

    async def extract_text(self, image_source: str) -> str:
        """Extract all visible raw text from an image using dedicated OCR."""
        result = ocr_service.extract_text(image_source)
        return result.get("text", "")

    async def extract_nameplate_data(self, image_source: str) -> Dict[str, Any]:
        """
        Extract structured nameplate / rating plate data (Manufacturer, Model, Serial, Voltage, Current, RPM).
        """
        prompt = (
            "You are an industrial OCR specialist extracting equipment nameplate data.\n"
            "Extract the following fields if visible in the image:\n"
            "- Manufacturer / Brand\n"
            "- Model / Part Number\n"
            "- Serial Number (S/N)\n"
            "- Voltage / Phase / Frequency\n"
            "- Full Load Amps (FLA)\n"
            "- Power Rating (kW or HP)\n"
            "- Operating RPM\n"
            "- Year of Manufacture\n\n"
            "Output the extracted information in clean structured key-value format."
        )
        extracted = await vision_service.analyze_image(image_source, prompt)
        return {
            "model_used": self.model,
            "structured_nameplate": extracted
        }


industrial_ocr = IndustrialOCR()
