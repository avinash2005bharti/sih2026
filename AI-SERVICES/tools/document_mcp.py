async def read_pdf(**kwargs):
    return {"success": True, "output": "document.read_pdf not implemented"}

async def extract_text(**kwargs):
    return {"success": True, "output": "document.extract_text not implemented"}

async def extract_tables(**kwargs):
    return {"success": True, "output": "document.extract_tables not implemented"}

async def metadata(**kwargs):
    return {"success": True, "output": "document.metadata not implemented"}

document_mcp_tools = {
    "document.read_pdf": read_pdf,
    "document.extract_text": extract_text,
    "document.extract_tables": extract_tables,
    "document.metadata": metadata
}
