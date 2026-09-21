"""
OCR MCP Tools for Sovereign AI Workbench.
Connects directly to Sovereign OCR Service for high-precision text extraction from scanned documents.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from ocr.ocr_service import ocr_service

def _resolve_file(path_str: str) -> str:
    if not path_str:
        return ""
    try:
        from tools.agent_tools import resolve_any_file_path
        p = resolve_any_file_path(path_str, must_exist=False)
        if p.exists():
            return str(p.resolve())
    except Exception:
        pass
    p = Path(path_str)
    if p.exists():
        return str(p.resolve())
    return path_str

async def extract_text(image_path: str = "", file_path: str = "", path: str = "", document_path: str = "", target: str = "", **kwargs) -> Dict[str, Any]:
    try:
        raw_target = image_path or file_path or path or document_path or target or kwargs.get("filename", "")
        resolved = _resolve_file(raw_target)
        res = ocr_service.extract_text(resolved)
        success = res.get("success", False) or bool(res.get("text", "").strip())
        return {
            "status": "ok" if success else "error",
            "success": success,
            "text": res.get("text", ""),
            "confidence": res.get("confidence", 1.0),
            "blocks": res.get("blocks", []),
            "lines": res.get("lines", res.get("blocks", [])),
            "line_count": res.get("line_count", len(res.get("blocks", []))),
            "page_count": res.get("page_count", 1),
            "pages": res.get("pages", []),
            "error": res.get("error") if not success else None
        }
    except Exception as e:
        return {"success": False, "error": str(e), "text": ""}

async def extract_document(image_path: str = "", **kwargs) -> Dict[str, Any]:
    return await extract_text(image_path=image_path, **kwargs)

async def extract_page(image_path: str = "", **kwargs) -> Dict[str, Any]:
    return await extract_text(image_path=image_path, **kwargs)

ocr_mcp_tools = {
    "ocr.extract_text": extract_text,
    "ocr.extract_document": extract_document,
    "ocr.extract_page": extract_page
}

ocr_extract_text = extract_text

