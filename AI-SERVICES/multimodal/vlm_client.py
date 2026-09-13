"""
Vision-Language Model (VLM) client for Sovereign AI Workbench.
Specialized in industrial visual inspection, equipment anomaly detection,
P&ID diagram analysis, and analog/digital meter readings using open-weight qwen2.5vl:3b.
"""

from typing import Any, Dict, List, Optional
from multimodal.vision import vision_service
from core.config import settings
from core.logging import logger


class VLMClient:
    """High-level client for industrial vision tasks using qwen2.5vl:3b."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.OLLAMA_VISION_MODEL
        logger.info(f"VLMClient initialized with model: {self.model}")

    async def inspect_equipment(self, image_source: str, equipment_type: str = "industrial machine") -> Dict[str, Any]:
        """
        Inspect equipment photo for visible wear, leaks, corrosion, crack, or misalignments.
        """
        prompt = (
            f"You are an industrial quality and maintenance inspector examining a {equipment_type}.\n"
            "Analyze this image and report:\n"
            "1. Visible equipment components identified\n"
            "2. Surface condition (corrosion, oil/fluid leaks, thermal discoloration, physical damage)\n"
            "3. Safety hazards or loose fittings\n"
            "4. Overall severity rating: NORMAL, MONITOR, or CRITICAL\n"
            "5. Recommended maintenance inspection action"
        )
        result = await vision_service.analyze_image(image_source, prompt)
        return {
            "equipment_type": equipment_type,
            "model_used": self.model,
            "analysis": result
        }

    async def read_analog_gauge(self, image_source: str) -> Dict[str, Any]:
        """
        Read needle position, value, unit, and scale from an analog dial/gauge image.
        """
        prompt = (
            "Examine the dial/gauge in this image carefully.\n"
            "Identify and extract:\n"
            "1. Measured value indicated by the needle/pointer\n"
            "2. Measurement units (e.g. PSI, bar, °C, RPM, kPa)\n"
            "3. Full scale range (min and max on dial)\n"
            "4. Is the reading in the normal (green), caution (yellow), or danger (red) zone?"
        )
        result = await vision_service.analyze_image(image_source, prompt)
        return {
            "model_used": self.model,
            "gauge_reading": result
        }

    async def analyze_diagram(self, image_source: str, diagram_type: str = "P&ID schematic") -> Dict[str, Any]:
        """
        Analyze an engineering schematic, single-line diagram, or P&ID.
        """
        prompt = (
            f"Analyze this engineering {diagram_type}.\n"
            "1. Identify main process flow lines and directions\n"
            "2. List identified valves, pumps, compressors, and instruments with their tag numbers (e.g. PT-101, V-204)\n"
            "3. Trace connections between major vessels\n"
            "4. Note any safety relief valves (PSV) or interlocks"
        )
        result = await vision_service.analyze_image(image_source, prompt)
        return {
            "diagram_type": diagram_type,
            "model_used": self.model,
            "analysis": result
        }


vlm_client = VLMClient()
