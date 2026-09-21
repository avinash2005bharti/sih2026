"""
Centralized Tool Registry for Sovereign AI Workbench.
Defines and registers all 16 required tools with strict schemas, safe execution, and sandboxing.

Required Tools:
1. document_parser
2. ocr
3. image_analyzer
4. rag_search
5. qdrant_search
6. neo4j_search
7. memory_search
8. python_executor
9. code_executor
10. spreadsheet_reader
11. spreadsheet_writer
12. pdf_generator
13. docx_generator
14. report_generator
15. file_reader
16. file_writer
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logging import logger
from core.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
SANDBOX_DIR = (BASE_DIR / "workspace").resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = (SANDBOX_DIR / "reports").resolve()
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_safe_path(filepath: str) -> Path:
    """Resolve filepath strictly inside SANDBOX_DIR, preventing directory traversal."""
    cleaned = filepath.replace("\\", "/").strip().lstrip("/")
    target = (SANDBOX_DIR / cleaned).resolve()
    try:
        if not target.is_relative_to(SANDBOX_DIR):
            raise PermissionError(f"Access denied: '{filepath}' attempts to escape workspace sandbox.")
    except AttributeError:
        if not str(target).startswith(str(SANDBOX_DIR)):
            raise PermissionError(f"Access denied: '{filepath}' attempts to escape workspace sandbox.")
    return target


class SovereignTool:
    """Standard base class for all registered tools."""

    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "error": {"type": "string"},
            "result": {"type": "object"}
        },
        "required": ["success"]
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool asynchronously."""
        raise NotImplementedError

    async def arun(self, **kwargs) -> Any:
        """Alias for async execute."""
        return await self.execute(**kwargs)

    def run(self, **kwargs) -> Any:
        """Synchronous execution wrapper."""
        return asyncio.run(self.execute(**kwargs))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema
        }


# ============================================================
# 1. document_parser
# ============================================================
class DocumentParserTool(SovereignTool):
    name = "document_parser"
    description = "Extracts text, metadata, and structural sections from documents (PDF, DOCX, XLSX, TXT, CSV, MD)."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Relative or absolute path to document file"}
        },
        "required": ["file_path"]
    }

    async def execute(self, file_path: str = "", **kwargs) -> Dict[str, Any]:
        try:
            from rag.parser import document_parser
            target = resolve_safe_path(file_path) if not Path(file_path).is_absolute() else Path(file_path)
            if not target.exists():
                # check uploads cache
                cand = BASE_DIR / "data" / "uploads" / Path(file_path).name
                if cand.exists():
                    target = cand
                else:
                    return {"success": False, "error": f"File not found: {file_path}"}

            parsed = document_parser.parse_file(str(target))
            return {
                "success": True,
                "filename": target.name,
                "character_count": len(parsed.text),
                "text": parsed.text[:10000],
                "metadata": parsed.metadata
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 2. ocr
# ============================================================
class OCRTool(SovereignTool):
    name = "ocr"
    description = "Extracts exact printed and alphanumeric text from images or scanned documents using PaddleOCR."
    input_schema = {
        "type": "object",
        "properties": {
            "image_path": {"type": "string", "description": "Path to image file or base64 data string"}
        },
        "required": ["image_path"]
    }

    async def execute(self, image_path: str = "", **kwargs) -> Dict[str, Any]:
        try:
            from ocr.ocr_service import ocr_service
            source = image_path
            if not image_path.startswith("data:") and len(image_path) < 500:
                p = resolve_safe_path(image_path) if not Path(image_path).is_absolute() else Path(image_path)
                if p.exists() and p.is_file():
                    source = str(p)
                else:
                    return {"success": False, "error": f"Document/image not found at '{image_path}'. Ingest file or check filename."}

            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, ocr_service.extract_text, source)
            return {"success": res.get("status") == "ok", "text": res.get("text", ""), "blocks": res.get("blocks", [])}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 3. image_analyzer
# ============================================================
class ImageAnalyzerTool(SovereignTool):
    name = "image_analyzer"
    description = "Inspects visual industrial imagery using Moondream vision model to describe defects, scenes, and machinery."
    input_schema = {
        "type": "object",
        "properties": {
            "image_path": {"type": "string", "description": "Path to image file or base64 string"},
            "prompt": {"type": "string", "description": "Specific inspection prompt"}
        },
        "required": ["image_path"]
    }

    async def execute(self, image_path: str = "", prompt: str = "Describe this industrial scene in detail", **kwargs) -> Dict[str, Any]:
        try:
            from vision.vision_service import vision_service
            source = image_path
            if not image_path.startswith("data:") and len(image_path) < 500:
                p = resolve_safe_path(image_path) if not Path(image_path).is_absolute() else Path(image_path)
                if p.exists() and p.is_file():
                    source = str(p)
                else:
                    return {"success": False, "error": f"Image file not found at '{image_path}'."}

            res = await vision_service.analyze_visual_scene(source, prompt=prompt)
            return {"success": True, "description": res.get("description", ""), "analysis": res}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 4. rag_search
# ============================================================
class RAGSearchTool(SovereignTool):
    name = "rag_search"
    description = "Retrieves evidence-grounded document chunks from Qdrant with similarity scores and exact citations."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query or question"},
            "top_k": {"type": "integer", "description": "Number of evidence chunks to retrieve (default 5)"},
            "document_id": {"type": "string", "description": "Optional document_id filter"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str = "", top_k: int = 5, document_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            from rag.retriever import rag_retriever
            results = await rag_retriever.retrieve(query=query, top_k=top_k, document_id=document_id)
            return {
                "success": True,
                "query": query,
                "count": len(results),
                "chunks": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 5. qdrant_search
# ============================================================
class QdrantSearchTool(SovereignTool):
    name = "qdrant_search"
    description = "Performs raw vector similarity queries directly against Qdrant vector database."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Query text to embed and search"},
            "collection": {"type": "string", "description": "Collection name (default: sovereign_documents)"},
            "limit": {"type": "integer", "description": "Maximum points to return"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str = "", collection: Optional[str] = None, limit: int = 5, **kwargs) -> Dict[str, Any]:
        try:
            from rag.embeddings import embeddings_service
            from rag.qdrant_client import qdrant_client
            vec = await embeddings_service.embed_text(query)
            hits = await qdrant_client.search(query_vector=vec, limit=limit)
            return {"success": True, "total_hits": len(hits), "results": hits}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 6. neo4j_search
# ============================================================
class Neo4jSearchTool(SovereignTool):
    name = "neo4j_search"
    description = "Searches knowledge graph entities, relationships, and equipment ontologies in Neo4j."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Entity name or Cypher query string"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str = "", **kwargs) -> Dict[str, Any]:
        try:
            from memory.graph.neo4j_service import neo4j_service
            res = await neo4j_service.search(query=query)
            return {"success": True, "query": query, "entities": res}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 7. memory_search
# ============================================================
class MemorySearchTool(SovereignTool):
    name = "memory_search"
    description = "Searches short-term, long-term episodic, and entity memory for user preferences and past findings."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Query to search in memory"},
            "user_id": {"type": "string", "description": "User identifier"},
            "limit": {"type": "integer", "description": "Number of memories to recall"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str = "", user_id: str = "default_user", limit: int = 5, **kwargs) -> Dict[str, Any]:
        try:
            from memory.memory_manager import memory_manager
            ctx = await memory_manager.get_context(query=query, user_id=user_id)
            return {"success": True, "memory_context": ctx}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 8. python_executor
# ============================================================
class PythonExecutorTool(SovereignTool):
    name = "python_executor"
    description = "Safely executes Python scripts in an isolated subprocess rooted inside the workspace sandbox."
    input_schema = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python source code to execute"},
            "timeout_seconds": {"type": "integer", "description": "Maximum execution time (default 30)"}
        },
        "required": ["code"]
    }

    async def execute(self, code: str = "", timeout_seconds: int = 30, **kwargs) -> Dict[str, Any]:
        try:
            # Block risky keywords
            disallowed = ["os.system", "shutil.rmtree", "subprocess.Popen", "__import__('os').system"]
            for d in disallowed:
                if d in code:
                    return {"success": False, "error": f"Security restriction: '{d}' is disallowed in python sandbox."}

            python_bin = sys.executable
            loop = asyncio.get_running_loop()

            def _run():
                proc = subprocess.run(
                    [python_bin, "-c", code],
                    cwd=str(SANDBOX_DIR),
                    capture_output=True,
                    text=True,
                    timeout=min(timeout_seconds, 60)
                )
                return proc.stdout, proc.stderr, proc.returncode

            stdout, stderr, code_ret = await loop.run_in_executor(None, _run)
            return {
                "success": code_ret == 0,
                "stdout": stdout[:10000],
                "stderr": stderr[:5000],
                "exit_code": code_ret
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Execution timed out after {timeout_seconds}s", "exit_code": 124}
        except Exception as e:
            return {"success": False, "error": str(e), "exit_code": 1}


# ============================================================
# 9. code_executor
# ============================================================
class CodeExecutorTool(PythonExecutorTool):
    name = "code_executor"
    description = "Executes computational logic, data transformation, or automation scripts in the sandbox."


# ============================================================
# 10. spreadsheet_reader
# ============================================================
class SpreadsheetReaderTool(SovereignTool):
    name = "spreadsheet_reader"
    description = "Reads, parses, and filters tabular sheets from Microsoft Excel (.xlsx) and CSV files."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to spreadsheet (.xlsx or .csv)"},
            "max_rows": {"type": "integer", "description": "Maximum rows to read (default 100)"},
            "sheet_name": {"type": "string", "description": "Specific sheet tab to read"}
        },
        "required": ["file_path"]
    }

    async def execute(self, file_path: str = "", max_rows: int = 100, sheet_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            target = resolve_safe_path(file_path) if not Path(file_path).is_absolute() else Path(file_path)
            if not target.exists():
                return {"success": False, "error": f"Spreadsheet not found: {file_path}"}

            ext = target.suffix.lower()
            if ext == ".csv":
                import csv
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    reader = list(csv.reader(f))
                headers = reader[0] if reader else []
                rows = reader[1:max_rows + 1] if len(reader) > 1 else []
                return {"success": True, "headers": headers, "rows": rows, "total_rows": len(reader)}

            elif ext == ".xlsx":
                import openpyxl
                wb = openpyxl.load_workbook(str(target), read_only=True, data_only=True)
                active_sheet = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
                data = list(active_sheet.iter_rows(values_only=True))
                headers = [str(c or "") for c in data[0]] if data else []
                rows = [[str(c if c is not None else "") for c in r] for r in data[1:max_rows + 1]] if len(data) > 1 else []
                return {
                    "success": True,
                    "sheet": active_sheet.title,
                    "headers": headers,
                    "rows": rows,
                    "total_rows": len(data)
                }
            else:
                return {"success": False, "error": f"Unsupported spreadsheet format: {ext}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 11. spreadsheet_writer
# ============================================================
class SpreadsheetWriterTool(SovereignTool):
    name = "spreadsheet_writer"
    description = "Generates formatted, official Microsoft Excel (.xlsx) workbooks with headers, borders, and styling."
    input_schema = {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "description": "Output Excel filename (e.g. 'audit_report.xlsx')"},
            "headers": {"type": "array", "items": {"type": "string"}, "description": "Column header names"},
            "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "List of rows"},
            "title": {"type": "string", "description": "Optional title block on row 1"}
        },
        "required": ["file_name", "headers", "rows"]
    }

    async def execute(self, file_name: str, headers: List[str], rows: List[List[Any]], title: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            if not file_name.lower().endswith(".xlsx"):
                file_name = f"{file_name}.xlsx"

            target = resolve_safe_path(f"reports/{file_name}")
            target.parent.mkdir(parents=True, exist_ok=True)

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Data Sheet"

            curr_row = 1
            if title:
                ws.cell(row=curr_row, column=1, value=title)
                ws.cell(row=curr_row, column=1).font = Font(name="Segoe UI", size=14, bold=True, color="1E3A8A")
                curr_row += 2

            header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
            header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

            for col_idx, h in enumerate(headers, 1):
                cell = ws.cell(row=curr_row, column=col_idx, value=str(h))
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            curr_row += 1
            for r in rows:
                for col_idx, val in enumerate(r, 1):
                    ws.cell(row=curr_row, column=col_idx, value=str(val if val is not None else ""))
                curr_row += 1

            # Auto-fit column widths
            for col in ws.columns:
                max_len = max(len(str(c.value or "")) for c in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

            wb.save(str(target))
            rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
            return {
                "success": True,
                "file_path": rel_path,
                "rows_written": len(rows),
                "columns": len(headers),
                "download_url": f"/workspace/{rel_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 12. pdf_generator
# ============================================================
class PDFGeneratorTool(SovereignTool):
    name = "pdf_generator"
    description = "Compiles structured PDF documents containing paragraphs, headings, and data tables using ReportLab."
    input_schema = {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "description": "Output PDF filename"},
            "title": {"type": "string", "description": "Document title"},
            "content": {"type": "string", "description": "Body markdown or text content"},
            "table_data": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "Optional table rows"}
        },
        "required": ["file_name", "title", "content"]
    }

    async def execute(self, file_name: str, title: str, content: str, table_data: Optional[List[List[str]]] = None, **kwargs) -> Dict[str, Any]:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            if not file_name.lower().endswith(".pdf"):
                file_name = f"{file_name}.pdf"

            target = resolve_safe_path(f"reports/{file_name}")
            target.parent.mkdir(parents=True, exist_ok=True)

            doc = SimpleDocTemplate(str(target), pagesize=letter)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.HexColor("#1E3A8A"))
            body_style = ParagraphStyle("BodyStyle", parent=styles["BodyText"], fontSize=10, leading=14)

            story = [
                Paragraph(title, title_style),
                Spacer(1, 14)
            ]

            for line in content.split("\n"):
                line_clean = line.strip()
                if line_clean:
                    story.append(Paragraph(line_clean, body_style))
                    story.append(Spacer(1, 6))

            if table_data:
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(Spacer(1, 12))
                story.append(t)

            doc.build(story)
            rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
            return {
                "success": True,
                "file_path": rel_path,
                "download_url": f"/workspace/{rel_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 13. docx_generator
# ============================================================
class DOCXGeneratorTool(SovereignTool):
    name = "docx_generator"
    description = "Generates formatted Microsoft Word (.docx) documents with headings, bullet points, and tables."
    input_schema = {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "description": "Output DOCX filename"},
            "title": {"type": "string", "description": "Document title"},
            "sections": {"type": "array", "items": {"type": "object"}, "description": "Sections with headings and text"}
        },
        "required": ["file_name", "title"]
    }

    async def execute(self, file_name: str, title: str, sections: Optional[List[Dict[str, str]]] = None, content: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            import docx
            if not file_name.lower().endswith(".docx"):
                file_name = f"{file_name}.docx"

            target = resolve_safe_path(f"reports/{file_name}")
            target.parent.mkdir(parents=True, exist_ok=True)

            doc = docx.Document()
            doc.add_heading(title, level=0)

            if sections:
                for sec in sections:
                    h = sec.get("heading")
                    b = sec.get("body")
                    if h:
                        doc.add_heading(h, level=1)
                    if b:
                        doc.add_paragraph(b)
            elif content:
                for line in content.split("\n"):
                    l_str = line.strip()
                    if not l_str:
                        continue
                    if l_str.startswith("# "):
                        doc.add_heading(l_str[2:], level=1)
                    elif l_str.startswith("## "):
                        doc.add_heading(l_str[3:], level=2)
                    elif l_str.startswith("### "):
                        doc.add_heading(l_str[4:], level=3)
                    elif l_str.startswith(("- ", "* ")):
                        doc.add_paragraph(l_str[2:], style="List Bullet")
                    else:
                        doc.add_paragraph(l_str)

            doc.save(str(target))
            rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
            return {
                "success": True,
                "file_path": rel_path,
                "download_url": f"/workspace/{rel_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 14. report_generator
# ============================================================
class ReportGeneratorTool(SovereignTool):
    name = "report_generator"
    description = "Produces a structured markdown report synthesizing findings, telemetry, and citations."
    input_schema = {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "description": "Report filename (e.g. 'Turbine_Risk_Report.md')"},
            "title": {"type": "string", "description": "Report Title"},
            "content": {"type": "string", "description": "Full markdown report content"}
        },
        "required": ["file_name", "title", "content"]
    }

    async def execute(self, file_name: str, title: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            if not file_name.lower().endswith(".md"):
                file_name = f"{file_name}.md"

            target = resolve_safe_path(f"reports/{file_name}")
            target.parent.mkdir(parents=True, exist_ok=True)

            full_text = f"# {title}\n\n{content}\n"
            with open(target, "w", encoding="utf-8") as f:
                f.write(full_text)

            rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
            return {
                "success": True,
                "file_path": rel_path,
                "bytes_written": len(full_text.encode("utf-8")),
                "download_url": f"/workspace/{rel_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 15. file_reader
# ============================================================
class FileReaderTool(SovereignTool):
    name = "file_reader"
    description = "Safely reads text content from files located inside the workspace sandbox."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "File path inside workspace sandbox"}
        },
        "required": ["file_path"]
    }

    async def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        try:
            target = resolve_safe_path(file_path)
            if not target.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return {"success": True, "file_path": file_path, "content": text[:50000]}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 16. file_writer
# ============================================================
class FileWriterTool(SovereignTool):
    name = "file_writer"
    description = "Safely writes text content to a file inside the workspace sandbox."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Target relative file path"},
            "content": {"type": "string", "description": "Text content to write"}
        },
        "required": ["file_path", "content"]
    }

    async def execute(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            target = resolve_safe_path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
            return {"success": True, "file_path": rel_path, "bytes_written": len(content.encode("utf-8"))}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# 17. list_documents
# ============================================================
class ListDocumentsTool(SovereignTool):
    name = "list_documents"
    description = "List all uploaded and indexed technical documents, manuals, SOPs, and reports in the workspace Document Section repository."
    input_schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "Maximum number of documents to return", "default": 50},
            "search_term": {"type": "string", "description": "Optional search filter for document name or type"}
        }
    }

    async def execute(self, limit: int = 50, search_term: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            from rag.document_store import document_store
            user_id = kwargs.get("user_id")
            is_admin = kwargs.get("is_admin", True)
            docs = document_store.list_documents(limit=limit, search_term=search_term, user_id=user_id, is_admin=is_admin)
            summary = []
            for d in docs:
                chunks = d.get("metadata", {}).get("chunksCount", "N/A") if isinstance(d.get("metadata"), dict) else "N/A"
                summary.append({
                    "document_id": d.get("document_id") or d.get("_id"),
                    "name": d.get("name"),
                    "type": d.get("documentType", "unknown"),
                    "status": d.get("processingStatus", "uploaded"),
                    "chunks_indexed": chunks,
                    "file_size": d.get("fileSize", 0),
                    "file_path": d.get("filePath") or d.get("file_path", "")
                })
            return {
                "success": True,
                "total_documents": len(summary),
                "documents": summary
            }
        except Exception as e:
            logger.error(f"[ListDocumentsTool] Error: {e}")
            return {"success": False, "error": str(e), "documents": []}


# ============================================================
# 18. get_document
# ============================================================
class GetDocumentTool(SovereignTool):
    name = "get_document"
    description = "Retrieve details, metadata, and extracted text for a specific document by its ID or title from the Document Section."
    input_schema = {
        "type": "object",
        "properties": {
            "document_id_or_name": {"type": "string", "description": "Document ID, title, or filename"}
        },
        "required": ["document_id_or_name"]
    }

    async def execute(self, document_id_or_name: str = "", **kwargs) -> Dict[str, Any]:
        try:
            doc_id = (
                document_id_or_name
                or kwargs.get("name_or_id")
                or kwargs.get("file_name_or_id")
                or kwargs.get("document_id")
                or kwargs.get("name")
                or kwargs.get("filename")
                or kwargs.get("file_name")
                or kwargs.get("file_path")
                or kwargs.get("doc_id")
                or kwargs.get("id")
            )
            from rag.document_store import document_store
            user_id = kwargs.get("user_id")
            is_admin = kwargs.get("is_admin", True)
            doc = document_store.get_document(doc_id_or_name=doc_id, user_id=user_id, is_admin=is_admin)
            if not doc:
                return {"success": False, "error": f"Document '{doc_id}' not found in document section"}
            return {"success": True, "document": doc}
        except Exception as e:
            logger.error(f"[GetDocumentTool] Error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# 19. get_document_content
# ============================================================
class GetDocumentContentTool(SovereignTool):
    name = "get_document_content"
    description = "Retrieve the complete, un-truncated full text content and technical details of an uploaded or repository document from the Document Section."
    input_schema = {
        "type": "object",
        "properties": {
            "document_id_or_name": {"type": "string", "description": "Document ID, title, or filename to read"}
        },
        "required": ["document_id_or_name"]
    }

    async def execute(self, document_id_or_name: str = "", **kwargs) -> Dict[str, Any]:
        try:
            doc_id = (
                document_id_or_name
                or kwargs.get("name_or_id")
                or kwargs.get("file_name_or_id")
                or kwargs.get("document_id")
                or kwargs.get("name")
                or kwargs.get("filename")
                or kwargs.get("file_name")
                or kwargs.get("file_path")
                or kwargs.get("doc_id")
                or kwargs.get("id")
            )
            from rag.document_store import document_store
            user_id = kwargs.get("user_id")
            is_admin = kwargs.get("is_admin", True)
            doc = document_store.get_document(doc_id_or_name=doc_id, user_id=user_id, is_admin=is_admin)
            if not doc:
                return {"success": False, "error": f"Document '{doc_id}' was not found in Document Section"}
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
            logger.error(f"[GetDocumentContentTool] Error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# 20. search_database_documents
# ============================================================
class SearchDatabaseDocumentsTool(SovereignTool):
    name = "search_database_documents"
    description = "Search across all uploaded technical manuals, SOPs, and database documents in the Document Section for specific parameters, keywords, and references."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keywords, phrases, or equipment tags to search"},
            "limit": {"type": "integer", "description": "Maximum matching documents to return", "default": 5}
        },
        "required": ["query"]
    }

    async def execute(self, query: str = "", limit: int = 5, **kwargs) -> Dict[str, Any]:
        try:
            q = query or kwargs.get("search_term") or kwargs.get("term") or ""
            from rag.document_store import document_store
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
            logger.error(f"[SearchDatabaseDocumentsTool] Error: {e}")
            return {"success": False, "error": str(e), "results": []}


# ============================================================
# 21. create_document
# ============================================================
class CreateDocumentTool(SovereignTool):
    name = "create_document"
    description = "Create a new technical document, chunk its text, index into Qdrant vector database, and store in the Document Section."
    input_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Document title"},
            "content": {"type": "string", "description": "Document text content"},
            "document_type": {"type": "string", "description": "Document category (sop, manual, report, spec)", "default": "report"}
        },
        "required": ["title", "content"]
    }

    async def execute(self, title: str, content: str, document_type: str = "report", **kwargs) -> Dict[str, Any]:
        try:
            from rag.document_store import document_store
            user_id = kwargs.get("user_id")
            is_admin = kwargs.get("is_admin", True)
            user_role = kwargs.get("user_role")
            user_name = kwargs.get("user_name")
            user_email = kwargs.get("user_email")
            return await document_store.create_document(
                name=title,
                content=content,
                document_type=document_type,
                user_id=user_id,
                is_admin=is_admin,
                user_role=user_role,
                user_name=user_name,
                user_email=user_email
            )
        except Exception as e:
            logger.error(f"[CreateDocumentTool] Error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# 22. update_document
# ============================================================
class UpdateDocumentTool(SovereignTool):
    name = "update_document"
    description = "Update or modify an existing document in the Document Section with instructed data."
    input_schema = {
        "type": "object",
        "properties": {
            "document_id_or_name": {"type": "string", "description": "Document ID or name to update"},
            "title": {"type": "string", "description": "New title (optional)"},
            "content": {"type": "string", "description": "New content or data to append/replace (optional)"},
            "append": {"type": "boolean", "description": "Whether to append to existing content", "default": False}
        },
        "required": ["document_id_or_name"]
    }

    async def execute(self, document_id_or_name: str, title: Optional[str] = None, content: Optional[str] = None, append: bool = False, **kwargs) -> Dict[str, Any]:
        try:
            from rag.document_store import document_store
            patch_target = kwargs.get("patch_target")
            patch_replacement = kwargs.get("patch_replacement")
            return await document_store.update_document(
                doc_id_or_name=document_id_or_name,
                title=title,
                content=content,
                append=append,
                patch_target=patch_target,
                patch_replacement=patch_replacement
            )
        except Exception as e:
            logger.error(f"[UpdateDocumentTool] Error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# 23. delete_document
# ============================================================
class DeleteDocumentTool(SovereignTool):
    name = "delete_document"
    description = "Permanently delete a document from the Document Section repository, disk, and vector store."
    input_schema = {
        "type": "object",
        "properties": {
            "document_id_or_name": {"type": "string", "description": "Document ID or name to delete"}
        },
        "required": ["document_id_or_name"]
    }

    async def execute(self, document_id_or_name: str, **kwargs) -> Dict[str, Any]:
        try:
            from rag.document_store import document_store
            return await document_store.delete_document(doc_id_or_name=document_id_or_name)
        except Exception as e:
            logger.error(f"[DeleteDocumentTool] Error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# CENTRAL TOOL REGISTRY CLASS
# ============================================================
class CentralToolRegistry:
    """Singleton registry hosting all sovereign workbench and document tools."""

    def __init__(self):
        self._tools: Dict[str, SovereignTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        tools = [
            DocumentParserTool(),
            OCRTool(),
            ImageAnalyzerTool(),
            RAGSearchTool(),
            QdrantSearchTool(),
            Neo4jSearchTool(),
            MemorySearchTool(),
            PythonExecutorTool(),
            CodeExecutorTool(),
            SpreadsheetReaderTool(),
            SpreadsheetWriterTool(),
            PDFGeneratorTool(),
            DOCXGeneratorTool(),
            ReportGeneratorTool(),
            FileReaderTool(),
            FileWriterTool(),
            ListDocumentsTool(),
            GetDocumentTool(),
            GetDocumentContentTool(),
            SearchDatabaseDocumentsTool(),
            CreateDocumentTool(),
            UpdateDocumentTool(),
            DeleteDocumentTool(),
        ]
        for t in tools:
            self._tools[t.name] = t
            # Also register canonical aliases
            if t.name == "list_documents":
                self._tools["document.list"] = t
                self._tools["document_list"] = t
            elif t.name == "get_document":
                self._tools["document.get"] = t
                self._tools["document_get"] = t
            elif t.name == "get_document_content":
                self._tools["document.get_content"] = t
                self._tools["document.read"] = t
                self._tools["document_read"] = t
                self._tools["document_get_content"] = t
            elif t.name == "search_database_documents":
                self._tools["document.search"] = t
                self._tools["document.search_database"] = t
                self._tools["document_search"] = t
            elif t.name == "create_document":
                self._tools["document.create"] = t
                self._tools["document.index"] = t
            elif t.name == "update_document":
                self._tools["document.update"] = t
            elif t.name == "delete_document":
                self._tools["document.delete"] = t

        logger.info(f"[TOOL_REGISTRY] Registered {len(self._tools)} sovereign workbench tools.")

    def get_tool(self, name: str) -> Optional[SovereignTool]:
        """Retrieve tool by exact name or normalized alias."""
        if not name:
            return None
        if name in self._tools:
            return self._tools[name]
        cleaned = name.lower().strip().replace("-", "_")
        if cleaned in self._tools:
            return self._tools[cleaned]
        cleaned_dot = name.lower().strip().replace("_", ".")
        if cleaned_dot in self._tools:
            return self._tools[cleaned_dot]
        return None

    def list_tools(self) -> List[str]:
        """List registered tool names."""
        return list(self._tools.keys())

    def list_tool_definitions(self) -> List[Dict[str, Any]]:
        """List tool schemas for planner and specialists."""
        return [t.to_dict() for t in self._tools.values()]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Safely execute tool with timing and error isolation."""
        t = self.get_tool(name)
        if not t:
            return {"success": False, "error": f"Unknown tool: '{name}'. Registered: {self.list_tools()}"}

        start = time.time()
        try:
            logger.info(f"[TOOL] Executing '{name}' with args: {arguments}")
            res = await t.execute(**arguments)
            duration = round(time.time() - start, 3)
            logger.info(f"[TOOL] Completed '{name}' in {duration}s (success={res.get('success', True)})")
            ret = {
                "success": res.get("success", True),
                "tool": name,
                "duration_seconds": duration,
                "result": res
            }
            if isinstance(res, dict):
                for k, v in res.items():
                    if k not in ret:
                        ret[k] = v
            return ret
        except Exception as e:
            duration = round(time.time() - start, 3)
            logger.error(f"[TOOL] Execution error in '{name}': {e}", exc_info=True)
            return {
                "success": False,
                "tool": name,
                "duration_seconds": duration,
                "error": str(e)
            }


# Global tool registry singleton
central_tool_registry = CentralToolRegistry()
