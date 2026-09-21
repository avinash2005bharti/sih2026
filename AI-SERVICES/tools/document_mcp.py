"""
MCP Document Tools implementation for Sovereign AI Workbench.
Connects document operations to real parsers and repository storage.
"""

from pathlib import Path
from typing import Any, Dict
from rag.parser import document_parser
from rag.document_store import document_store
from core.logging import logger


async def read_pdf(file_path: str = "", **kwargs) -> Dict[str, Any]:
    """Extract and read full text from a PDF file."""
    try:
        if not file_path:
            # Fallback to checking document by name
            doc_name = kwargs.get("name") or kwargs.get("document_id")
            if doc_name:
                doc = document_store.get_document(doc_name)
                if doc and doc.get("filePath"):
                    file_path = doc["filePath"]
        
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"PDF file not found: {file_path}"}
            
        parsed = document_parser.parse_file(str(path))
        return {
            "success": True,
            "filename": path.name,
            "text": parsed.text,
            "length": len(parsed.text)
        }
    except Exception as e:
        logger.error(f"read_pdf error: {e}")
        return {"success": False, "error": str(e)}


async def extract_text(file_path: str = "", **kwargs) -> Dict[str, Any]:
    """Extract text from any supported document format."""
    try:
        path = Path(file_path)
        if not path.exists():
            doc_name = kwargs.get("name") or kwargs.get("document_id")
            if doc_name:
                doc = document_store.get_document(doc_name)
                if doc and doc.get("filePath"):
                    path = Path(doc["filePath"])

        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        parsed = document_parser.parse_file(str(path))
        return {
            "success": True,
            "filename": path.name,
            "text": parsed.text,
            "character_count": len(parsed.text),
            "metadata": parsed.metadata
        }
    except Exception as e:
        logger.error(f"extract_text error: {e}")
        return {"success": False, "error": str(e)}


async def extract_tables(file_path: str = "", **kwargs) -> Dict[str, Any]:
    """Extract tabular lines or sheets from document."""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        ext = path.suffix.lower()
        if ext == ".xlsx":
            return {"success": True, "tables": document_parser._parse_xlsx(path)}
        elif ext == ".csv":
            return {"success": True, "tables": document_parser._parse_csv(path)}
        elif ext in [".docx", ".doc"]:
            return {"success": True, "tables": document_parser._parse_docx(path)}
        else:
            return {"success": True, "tables": document_parser._parse_text(path)}
    except Exception as e:
        logger.error(f"extract_tables error: {e}")
        return {"success": False, "error": str(e)}


async def metadata(file_path: str = "", **kwargs) -> Dict[str, Any]:
    """Get metadata for document."""
    try:
        doc_query = file_path or kwargs.get("name") or kwargs.get("document_id")
        if doc_query:
            doc = document_store.get_document(doc_query)
            if doc:
                return {"success": True, "metadata": doc}

        path = Path(file_path)
        if path.exists():
            stat = path.stat()
            return {
                "success": True,
                "metadata": {
                    "filename": path.name,
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime
                }
            }
        return {"success": False, "error": f"Document metadata not found for '{doc_query}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def list_docs(limit: int = 50, search: str = "", **kwargs) -> Dict[str, Any]:
    """List repository documents from document section."""
    try:
        search_term = search or kwargs.get("search_term") or kwargs.get("query")
        user_id = kwargs.get("user_id")
        is_admin = kwargs.get("is_admin", True)
        docs = document_store.list_documents(limit=limit, search_term=search_term or None, user_id=user_id, is_admin=is_admin)
        return {"success": True, "count": len(docs), "documents": docs}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_doc(document_id: str = "", **kwargs) -> Dict[str, Any]:
    """Get metadata and details for a specific document."""
    try:
        doc_id = (
            document_id
            or kwargs.get("document_id_or_name")
            or kwargs.get("name_or_id")
            or kwargs.get("file_name_or_id")
            or kwargs.get("name")
            or kwargs.get("filename")
            or kwargs.get("file_name")
            or kwargs.get("file_path")
            or kwargs.get("doc_id")
            or kwargs.get("id")
        )
        user_id = kwargs.get("user_id")
        is_admin = kwargs.get("is_admin", True)
        doc = document_store.get_document(doc_id_or_name=doc_id, user_id=user_id, is_admin=is_admin)
        if not doc:
            return {"success": False, "error": f"Document '{doc_id}' not found in document section"}
        return {"success": True, "document": doc}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_doc_content(document_id: str = "", **kwargs) -> Dict[str, Any]:
    """Retrieve full un-truncated content and data of a document from document section."""
    try:
        doc_id = (
            document_id
            or kwargs.get("document_id_or_name")
            or kwargs.get("name_or_id")
            or kwargs.get("file_name_or_id")
            or kwargs.get("name")
            or kwargs.get("filename")
            or kwargs.get("file_name")
            or kwargs.get("file_path")
            or kwargs.get("doc_id")
            or kwargs.get("id")
        )
        user_id = kwargs.get("user_id")
        is_admin = kwargs.get("is_admin", True)
        doc = document_store.get_document(doc_id_or_name=doc_id, user_id=user_id, is_admin=is_admin)
        if not doc:
            return {"success": False, "error": f"Document '{doc_id}' not found in document section"}
        full_text = doc.get("content") or doc.get("full_text") or doc.get("extractedText") or ""
        return {
            "success": True,
            "document_id": doc.get("document_id") or doc.get("_id"),
            "name": doc.get("name") or doc.get("originalName"),
            "document_type": doc.get("documentType", "text"),
            "character_count": len(full_text),
            "content": full_text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def search_database_docs(query: str = "", limit: int = 5, **kwargs) -> Dict[str, Any]:
    """Search through all documents in document section for keywords or clauses."""
    try:
        q = query or kwargs.get("search_term") or kwargs.get("term") or ""
        user_id = kwargs.get("user_id")
        is_admin = kwargs.get("is_admin", True)
        matches = document_store.search_documents_content(query=q, limit=limit, user_id=user_id, is_admin=is_admin)
        return {
            "success": True,
            "query": q,
            "results_count": len(matches),
            "results": matches
        }
    except Exception as e:
        return {"success": False, "error": str(e), "results": []}


async def create_doc(title: str = "", content: str = "", **kwargs) -> Dict[str, Any]:
    """Create and index a document."""
    try:
        doc_type = kwargs.get("document_type", "report")
        user_id = kwargs.get("user_id")
        is_admin = kwargs.get("is_admin", True)
        user_role = kwargs.get("user_role")
        user_name = kwargs.get("user_name")
        user_email = kwargs.get("user_email")
        return await document_store.create_document(
            name=title,
            content=content,
            document_type=doc_type,
            user_id=user_id,
            is_admin=is_admin,
            user_role=user_role,
            user_name=user_name,
            user_email=user_email
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


async def update_doc(document_id: str = "", title: str = None, content: str = None, **kwargs) -> Dict[str, Any]:
    """Update and re-index a document."""
    try:
        doc_id = document_id or kwargs.get("doc_id") or kwargs.get("name") or kwargs.get("document_id_or_name")
        append = kwargs.get("append", False)
        patch_target = kwargs.get("patch_target")
        patch_replacement = kwargs.get("patch_replacement")
        return await document_store.update_document(
            doc_id_or_name=doc_id,
            title=title,
            content=content,
            append=append,
            patch_target=patch_target,
            patch_replacement=patch_replacement
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


async def delete_doc(document_id: str = "", **kwargs) -> Dict[str, Any]:
    """Delete a document and its vectors."""
    try:
        doc_id = document_id or kwargs.get("doc_id") or kwargs.get("name") or kwargs.get("document_id_or_name")
        return await document_store.delete_document(doc_id_or_name=doc_id)
    except Exception as e:
        return {"success": False, "error": str(e)}


document_mcp_tools = {
    "document.read_pdf": read_pdf,
    "document.extract_text": extract_text,
    "document.extract_tables": extract_tables,
    "document.metadata": metadata,
    "document.list": list_docs,
    "document.get": get_doc,
    "document.get_content": get_doc_content,
    "document.read": get_doc_content,
    "document.search": search_database_docs,
    "document.search_database": search_database_docs,
    "document.create": create_doc,
    "document.update": update_doc,
    "document.delete": delete_doc,
    "document.index": create_doc,
    # Standard non-prefix aliases
    "list_documents": list_docs,
    "get_document": get_doc,
    "get_document_content": get_doc_content,
    "search_database_documents": search_database_docs,
    "create_document": create_doc,
    "update_document": update_doc,
    "delete_document": delete_doc,
}
