async def extract_text(**kwargs):
    return {"success": True, "output": "ocr.extract_text not implemented"}

async def extract_document(**kwargs):
    return {"success": True, "output": "ocr.extract_document not implemented"}

async def extract_page(**kwargs):
    return {"success": True, "output": "ocr.extract_page not implemented"}

ocr_mcp_tools = {
    "ocr.extract_text": extract_text,
    "ocr.extract_document": extract_document,
    "ocr.extract_page": extract_page
}
