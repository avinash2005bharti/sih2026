import base64
from pathlib import Path
from typing import Any, Dict, Optional
from core.config import settings
from core.security import validate_safe_path
from core.logging import logger
from llm.ollama_client import ollama_client
from tools.base_tool import BaseTool, ToolResult

class ImageAnalyzerTool(BaseTool):
    name = "image_analyzer"
    description = "Analyze industrial equipment images, gauges, technical diagrams, and anomalies using Qwen2.5-VL 3B."
    input_schema = {
        "type": "object",
        "properties": {
            "image_path": {"type": "string", "description": "Path to image file"},
            "prompt": {"type": "string", "description": "Specific inspection question or instruction"}
        },
        "required": ["image_path"]
    }
    output_schema = {"type": "object", "properties": {"analysis": {"type": "string"}}}
    risk_level = "low"

    async def execute(self, image_path: str, prompt: str = "Perform a detailed industrial visual inspection of this image.", **kwargs) -> ToolResult:
        try:
            safe_path = validate_safe_path(image_path)
            if not safe_path.exists():
                return ToolResult(success=False, error=f"Image not found: {image_path}")

            # Encode image to base64
            img_bytes = safe_path.read_bytes()
            b64_img = base64.b64encode(img_bytes).decode("utf-8")

            messages = [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [b64_img]
                }
            ]

            resp = await ollama_client.chat(
                model=settings.DEFAULT_VISION_MODEL,
                messages=messages
            )
            analysis_text = resp.get("message", {}).get("content", "")

            return ToolResult(
                success=True,
                output=analysis_text,
                metadata={"image": safe_path.name, "model": settings.DEFAULT_VISION_MODEL}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Vision inspection failed: {str(e)}")
