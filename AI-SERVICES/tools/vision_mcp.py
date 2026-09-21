"""
Vision MCP Tools for Sovereign AI Workbench.
Connects directly to Sovereign Vision Service for visual reasoning and multimodal scene understanding.
"""

from typing import Dict, Any
from vision.vision_service import vision_service

async def analyze_image(image_path: str = "", prompt: str = "Analyze this image for equipment state, defects, and abnormalities.", **kwargs) -> Dict[str, Any]:
    try:
        res = await vision_service.analyze_visual_scene(image_source=image_path, prompt=prompt)
        return {
            "success": res.get("success", False),
            "description": res.get("description", ""),
            "model": res.get("model", "moondream"),
            "duration_seconds": res.get("duration_seconds", 0)
        }
    except Exception as e:
        return {"success": False, "error": str(e), "description": ""}

async def analyze_document_image(image_path: str = "", prompt: str = "Analyze document layout, visual diagrams, and stamps.", **kwargs) -> Dict[str, Any]:
    return await analyze_image(image_path=image_path, prompt=prompt, **kwargs)

vision_mcp_tools = {
    "vision.analyze_image": analyze_image,
    "vision.analyze_document_image": analyze_document_image
}
