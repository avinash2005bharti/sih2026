"""
Multimodal Orchestrator for Sovereign AI Workbench.
Coordinates Dedicated OCR (PaddleOCR) for exact text facts and Moondream for visual reasoning,
synthesizing both outputs into a unified multimodal context for downstream reasoning agents.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Union, AsyncGenerator
from PIL import Image

from ocr.ocr_service import ocr_service
from vision.vision_service import vision_service
from core.logging import logger
from core.config import settings


class MultimodalOrchestrator:
    """Orchestrates dedicated OCR and Moondream vision pipelines into unified intelligence."""

    def __init__(self):
        self.ocr = ocr_service
        self.vision = vision_service

    async def analyze(
        self,
        image_source: Optional[Union[str, bytes, Image.Image]] = None,
        user_prompt: Optional[str] = None,
        filename: Optional[str] = "inspection_image.jpg",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run both OCR and Moondream in parallel or sequential pipeline, combining outputs into Unified Context.

        Args:
            image_source: Base64 string, bytes, or file path (or image_input).
            user_prompt: Optional user query or instruction (or user_query).
            filename: Original file name.
            kwargs: Accepts image_input, user_query, progress_callback.

        Returns:
            Dict with ocr, vision, unified combined_context, and formatted agent_prompt.
        """
        start_time = time.time()
        
        # Support alias kwargs
        if image_source is None and "image_input" in kwargs:
            image_source = kwargs["image_input"]
        if user_prompt is None and "user_query" in kwargs:
            user_prompt = kwargs["user_query"]
        progress_cb = kwargs.get("progress_callback")

        logger.info(f"[MULTIMODAL] Starting combined multimodal analysis for {filename}")

        if progress_cb:
            try:
                progress_cb("ocr_start", "Extracting exact text via on-premise PaddleOCR")
            except Exception:
                pass

        # 1. Run Dedicated OCR (Exact text extraction)
        # Run in thread pool to avoid blocking the asyncio event loop during CPU inference
        loop = asyncio.get_running_loop()
        try:
            ocr_result = await loop.run_in_executor(None, self.ocr.extract_text, image_source)
            if progress_cb:
                progress_cb("ocr_complete", f"OCR extracted {ocr_result.get('line_count', len(ocr_result.get('blocks', [])))} lines")
        except Exception as ocr_err:
            logger.error(f"[MULTIMODAL] OCR execution failed: {ocr_err}")
            ocr_result = {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "blocks": [],
                "error": str(ocr_err)
            }

        # 2. Run Moondream Vision (Visual scene understanding)
        if progress_cb:
            try:
                progress_cb("vision_start", f"Running visual scene analysis via local {settings.VISION_MODEL}")
            except Exception:
                pass

        try:
            vision_result = await self.vision.analyze_visual_scene(image_source)
            if progress_cb:
                progress_cb("vision_complete", "Visual scene reasoning complete")
        except Exception as vis_err:
            logger.error(f"[MULTIMODAL] Vision model execution failed: {vis_err}")
            vision_result = {
                "success": False,
                "description": "Visual analysis unavailable due to model error.",
                "error": str(vis_err)
            }

        # 3. Combine outputs into Unified Context
        logger.info("[MULTIMODAL] Combining OCR + vision")
        combined_context = self.build_unified_context(
            ocr_text=ocr_result.get("text", ""),
            vision_description=vision_result.get("description", ""),
            user_query=user_prompt
        )

        agent_prompt = self.format_agent_prompt(
            unified_context=combined_context,
            user_query=user_prompt
        )

        total_duration = round(time.time() - start_time, 2)
        logger.info(f"[MULTIMODAL] Analysis completed in {total_duration}s")

        return {
            "success": bool(ocr_result.get("success") or vision_result.get("success")),
            "filename": filename,
            "ocr": {
                "text": ocr_result.get("text", ""),
                "confidence": ocr_result.get("confidence", 0.0),
                "blocks": ocr_result.get("blocks", []),
                "success": ocr_result.get("success", False),
                "error": ocr_result.get("error")
            },
            "vision": {
                "description": vision_result.get("description", ""),
                "model": vision_result.get("model", settings.VISION_MODEL),
                "success": vision_result.get("success", False),
                "error": vision_result.get("error")
            },
            "combined_context": combined_context,
            "unified_context": combined_context,
            "agent_prompt": agent_prompt,
            "duration_seconds": total_duration
        }

    def build_unified_context(
        self,
        ocr_text: str,
        vision_description: str,
        user_query: Optional[str] = None
    ) -> str:
        """
        Assemble clear, structured multimodal context combining OCR facts and Moondream observations.
        """
        sections = []

        if ocr_text and ocr_text.strip():
            sections.append(f"=== [EXACT ALPHANUMERIC FACTS (OCR)] ===\n{ocr_text.strip()}")
        else:
            sections.append("=== [EXACT ALPHANUMERIC FACTS (OCR)] ===\n[No visible text detected by OCR or OCR text extraction unavailable]")

        if vision_description and vision_description.strip():
            sections.append(f"=== [VISUAL SCENE UNDERSTANDING (MOONDREAM)] ===\n{vision_description.strip()}")
        else:
            sections.append("=== [VISUAL SCENE UNDERSTANDING (MOONDREAM)] ===\n[Visual scene analysis unavailable]")

        if user_query and user_query.strip():
            sections.append(f"=== [OPERATOR QUERY] ===\n{user_query.strip()}")

        return "\n\n".join(sections)

    def format_agent_prompt(
        self,
        unified_context: str,
        user_query: Optional[str] = None
    ) -> str:
        """
        Format prompt for the downstream reasoning LLM / Risk Agent.
        Enforces separation: OCR provides facts; Vision provides scene context.
        """
        query_text = user_query or "Perform an industrial inspection and risk assessment based on the provided image."
        return (
            f"You are the Sovereign Industrial Intelligence & Risk Assessment Agent.\n\n"
            f"MANDATORY ARCHITECTURAL RULE:\n"
            f"A field inspection image was processed by two independent local engines:\n"
            f"1. Dedicated OCR (PaddleOCR) extracted exact alphanumeric text (equipment IDs, ratings, gauges, timestamps).\n"
            f"2. Dedicated Vision Model (Moondream) analyzed visual features (objects, scene layout, physical damage, leakage, abnormalities).\n\n"
            f"=== MULTIMODAL INSPECTION DATA ===\n"
            f"{unified_context}\n"
            f"===================================\n\n"
            f"Analyze both sources systematically:\n"
            f"- State identified equipment and exact readings/specifications from the OCR data.\n"
            f"- Correlate with visual physical observations from the Vision model.\n"
            f"- Provide a rigorous Risk Assessment (rating: NORMAL, MONITOR, or CRITICAL).\n"
            f"- Provide specific, actionable Engineering Recommendations.\n\n"
            f"User Question: {query_text}"
        )

    # Alias for pipeline processing
    process_multimodal = analyze


# Global singleton instance
multimodal_orchestrator = MultimodalOrchestrator()
