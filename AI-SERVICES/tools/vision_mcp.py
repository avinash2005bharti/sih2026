async def analyze_image(**kwargs):
    return {"success": True, "output": "vision.analyze_image not implemented"}

async def analyze_document_image(**kwargs):
    return {"success": True, "output": "vision.analyze_document_image not implemented"}

vision_mcp_tools = {
    "vision.analyze_image": analyze_image,
    "vision.analyze_document_image": analyze_document_image
}
