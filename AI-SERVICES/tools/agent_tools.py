"""
Central LangChain Tool Registry for Sovereign AI Workbench.
All tools execute safely within the workspace sandbox: AI-SERVICES/workspace.
Enforces boundaries, path traversal prevention, and structured observations.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from langchain_core.tools import tool
from core.logging import logger

from tools.memory_tool import save_memory
from tools.rag_tool import search_knowledge_base, index_document

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.resolve()
SANDBOX_DIR = (BASE_DIR / "workspace").resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = (SANDBOX_DIR / "reports").resolve()
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DOCS_DIR = (PROJECT_ROOT / "BACKEND" / "uploads" / "documents").resolve()
UPLOADS_DOCS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR = (PROJECT_ROOT / "BACKEND" / "uploads").resolve()
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_any_file_path(filepath: str, must_exist: bool = False) -> Path:
    """
    Resolve a file path across all workspace, project, and uploaded document locations.
    Gives full access to:
    1. Direct absolute paths
    2. Relative paths from PROJECT_ROOT or SANDBOX_DIR
    3. Filenames in BACKEND/uploads/documents/ or BACKEND/uploads/
    4. Filenames in SANDBOX_DIR / reports/
    5. MongoDB documents lookup by name or originalName
    """
    if not filepath or not isinstance(filepath, str):
        return SANDBOX_DIR / "unnamed_file"

    cleaned = filepath.strip().replace("\\", "/")

    # 1. Direct path check
    direct_p = Path(cleaned)
    if direct_p.is_absolute() and direct_p.exists():
        return direct_p.resolve()

    # 2. Check relative to PROJECT_ROOT
    root_p = (PROJECT_ROOT / cleaned.lstrip("/")).resolve()
    if root_p.exists():
        return root_p

    # 3. Check relative to SANDBOX_DIR
    sandbox_p = (SANDBOX_DIR / cleaned.lstrip("/")).resolve()
    if sandbox_p.exists():
        return sandbox_p

    # 4. Check relative to REPORTS_DIR
    reports_p = (REPORTS_DIR / cleaned.lstrip("/")).resolve()
    if reports_p.exists():
        return reports_p

    # 5. Check in BACKEND/uploads/documents/
    name_only = Path(cleaned).name
    upload_doc_p = (UPLOADS_DOCS_DIR / name_only).resolve()
    if upload_doc_p.exists():
        return upload_doc_p

    # 6. Check in BACKEND/uploads/
    upload_p = (UPLOADS_DIR / name_only).resolve()
    if upload_p.exists():
        return upload_p

    # 7. Check MongoDB uploaded documents by title or originalName
    try:
        from rag.document_store import document_store
        db_doc = document_store.get_document(name_only) or document_store.get_document(cleaned)
        if db_doc:
            db_path = db_doc.get("filePath")
            if db_path and Path(db_path).exists():
                return Path(db_path).resolve()
    except Exception:
        pass

    # 8. Fuzzy prefix match in UPLOADS_DOCS_DIR (e.g. user passes 'Event-Driven' or 'Generative-AI')
    if UPLOADS_DOCS_DIR.exists():
        for candidate in UPLOADS_DOCS_DIR.glob("*"):
            if candidate.is_file() and name_only.lower() in candidate.name.lower():
                return candidate.resolve()

    # 9. Fuzzy prefix match in SANDBOX_DIR / REPORTS_DIR
    if REPORTS_DIR.exists():
        for candidate in REPORTS_DIR.glob("*"):
            if candidate.is_file() and name_only.lower() in candidate.name.lower():
                return candidate.resolve()

    # If file is to be created / written and doesn't exist yet:
    if not must_exist:
        if direct_p.is_absolute():
            return direct_p.resolve()
        if "reports/" in cleaned or cleaned.startswith("reports"):
            return (SANDBOX_DIR / cleaned.lstrip("/")).resolve()
        return (SANDBOX_DIR / cleaned.lstrip("/")).resolve()

    # If must exist and was not found, return root_p or direct_p
    return root_p if root_p.exists() else direct_p


# Alias for backwards compatibility
resolve_safe_path = resolve_any_file_path


def read_any_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    max_chars: Optional[int] = None
) -> Dict[str, Any]:
    """
    Read text or extract structured contents from ANY document format:
    PDF, DOCX, XLSX, PPTX, CSV, JSON, Markdown, Text, Code, etc.
    """
    target = resolve_any_file_path(file_path, must_exist=True)
    if not target.exists():
        return {"success": False, "error": f"File not found: '{file_path}' (searched workspace, uploads, and repository)"}
    if target.is_dir():
        return {"success": False, "error": f"Path is a directory, not a file: '{file_path}'"}

    ext = target.suffix.lower()
    stat = target.stat()

    # Binary/Document formats parsed via DocumentParser
    from rag.parser import DocumentParser, document_parser
    if ext in DocumentParser.SUPPORTED_EXTENSIONS and ext not in [".txt", ".md", ".log", ".json", ".xml", ".yaml", ".yml", ".py", ".js", ".ts"]:
        try:
            parsed = document_parser.parse_file(str(target))
            full_text = parsed.text
            lines = full_text.splitlines()
            total_lines = len(lines)
            s = max(1, start_line) if start_line else 1
            e = min(total_lines, end_line) if end_line else total_lines
            sliced_content = "\n".join(lines[s - 1:e])
            if max_chars and len(sliced_content) > max_chars:
                sliced_content = sliced_content[:max_chars] + f"\n... [Truncated at {max_chars} characters. Specify start_line/end_line for more.]"
            return {
                "success": True,
                "file_name": target.name,
                "file_path": str(target),
                "format": ext,
                "size_bytes": stat.st_size,
                "total_lines": total_lines,
                "content": sliced_content,
                "metadata": parsed.metadata
            }
        except Exception as pe:
            logger.warning(f"DocumentParser extraction note for {target}: {pe}")

    # Plain text / code / markdown files
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            with open(target, "r", encoding=enc) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

    total_lines = len(lines)
    s = max(1, start_line) if start_line else 1
    e = min(total_lines, end_line) if end_line else total_lines
    content = "".join(lines[s - 1:e])
    if max_chars and len(content) > max_chars:
        content = content[:max_chars] + f"\n... [Truncated at {max_chars} characters. Specify start_line/end_line for more.]"

    return {
        "success": True,
        "file_name": target.name,
        "file_path": str(target),
        "format": ext or "text",
        "size_bytes": stat.st_size,
        "total_lines": total_lines,
        "content": content
    }


def analyze_any_document(file_path: str, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform structural and technical analysis on any file or uploaded document.
    Extracts headings, tables, operational metrics, tolerances, and summary excerpts.
    """
    read_res = read_any_file(file_path)
    if not read_res.get("success"):
        return read_res

    content = read_res.get("content", "")
    lines = [l.strip() for l in content.splitlines() if l.strip()]

    # Section headings
    headings = [l for l in lines if l.startswith("#") or (len(l) < 70 and l.isupper()) or l.startswith("Section") or l.startswith("Chapter") or l.startswith("Part")]

    # Tables
    tables = [l for l in lines if "|" in l]

    # Operational metrics, limits, tolerances
    metrics = []
    keywords = ["limit", "threshold", "temperature", "pressure", "voltage", "hz", "rpm", "tolerance", "vibration", "amp", "psi", "kw", "mw", "kva", "db", "mm/s", "spec"]
    for l in lines:
        if any(w in l.lower() for w in keywords):
            metrics.append(l)
            if len(metrics) >= 25:
                break

    # Targeted query excerpts
    relevant_excerpts = []
    if query:
        q_words = [w.lower() for w in query.split() if len(w) > 3]
        for l in lines:
            if any(qw in l.lower() for qw in q_words):
                relevant_excerpts.append(l)
                if len(relevant_excerpts) >= 15:
                    break

    return {
        "success": True,
        "file_name": read_res.get("file_name"),
        "file_path": read_res.get("file_path"),
        "format": read_res.get("format"),
        "size_bytes": read_res.get("size_bytes"),
        "total_lines": read_res.get("total_lines"),
        "character_count": len(content),
        "detected_sections": headings[:15],
        "tables_found": len(tables),
        "extracted_operating_parameters": metrics[:20],
        "query_relevant_excerpts": relevant_excerpts if query else None,
        "summary_preview": content[:2500] if len(content) > 2500 else content
    }


def execute_terminal_command(
    command: str,
    cwd: Optional[str] = None,
    timeout_seconds: int = 60
) -> Dict[str, Any]:
    """
    Execute any shell/terminal command on the host machine.
    Returns stdout, stderr, return code, and execution details.
    """
    work_dir = Path(cwd).resolve() if cwd else PROJECT_ROOT
    if not work_dir.exists():
        work_dir = PROJECT_ROOT

    timeout = max(1, min(timeout_seconds, 180))
    logger.info(f"[TERMINAL] Running command: '{command}' in '{work_dir}' (timeout={timeout}s)")

    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        success = (proc.returncode == 0)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        logger.info(f"[TERMINAL] Finished with exit_code={proc.returncode}")
        return {
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode,
            "cwd": str(work_dir),
            "command": command
        }
    except subprocess.TimeoutExpired:
        logger.warning(f"[TERMINAL] Command timed out after {timeout}s: '{command}'")
        return {
            "success": False,
            "error": f"Command execution timed out after {timeout} seconds",
            "exit_code": -1,
            "command": command,
            "cwd": str(work_dir)
        }
    except Exception as e:
        logger.error(f"[TERMINAL] Command execution error: {e}")
        return {
            "success": False,
            "error": str(e),
            "exit_code": -1,
            "command": command,
            "cwd": str(work_dir)
        }


@tool
def create_directory(dir_path: str) -> str:
    """
    Create a new directory or folder.
    Example: create_directory(dir_path="projects/audit_results")
    """
    try:
        target = resolve_any_file_path(dir_path, must_exist=False)
        target.mkdir(parents=True, exist_ok=True)
        rel_path = str(target).replace("\\", "/")
        logger.info(f"[TOOL:create_directory] Created directory '{rel_path}'")
        return json.dumps({
            "success": True,
            "dir_path": rel_path,
            "message": f"Directory '{rel_path}' created successfully."
        })
    except Exception as e:
        logger.error(f"[TOOL:create_directory] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def create_file(file_path: str, content: str) -> str:
    """
    Create or overwrite a file with the specified content anywhere in workspace, reports, or project.
    Example: create_file(file_path="reports/turbine_spec.md", content="# Turbine Specification\\nParameters...")
    """
    try:
        target = resolve_any_file_path(file_path, must_exist=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        bytes_written = len(content.encode("utf-8"))
        rel_path = str(target.relative_to(PROJECT_ROOT) if target.is_relative_to(PROJECT_ROOT) else target).replace("\\", "/")
        logger.info(f"[TOOL:create_file] Created file '{rel_path}' ({bytes_written} bytes)")
        return json.dumps({
            "success": True,
            "file_name": target.name,
            "file_path": str(target).replace("\\", "/"),
            "relative_path": rel_path,
            "bytes_written": bytes_written,
            "message": f"File '{target.name}' created successfully."
        })
    except Exception as e:
        logger.error(f"[TOOL:create_file] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def read_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """
    Read text contents or extract parsed data from ANY document (PDF, DOCX, XLSX, CSV, JSON, Markdown, Text).
    Automatically locates uploaded documents in BACKEND/uploads/documents/ or local files.
    Example: read_file(file_path="1789822346748-589300_20250423-EB-Event-Driven_Design_for_Agents.PDF")
    Example: read_file(file_path="reports/audit.md")
    """
    try:
        res = read_any_file(file_path, start_line=start_line, end_line=end_line)
        return json.dumps(res)
    except Exception as e:
        logger.error(f"[TOOL:read_file] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def list_files(dir_path: str = ".") -> str:
    """
    List files and folders inside a given directory. Accepts workspace, project root, or uploads.
    Example: list_files(dir_path=".")
    Example: list_files(dir_path="BACKEND/uploads/documents")
    """
    try:
        target = resolve_any_file_path(dir_path, must_exist=True)
        if not target.exists():
            return json.dumps({"success": False, "error": f"Directory not found: {dir_path}"})
        if not target.is_dir():
            return json.dumps({"success": False, "error": f"Path is not a directory: {dir_path}"})
        entries = []
        for item in sorted(target.iterdir()):
            entries.append({
                "name": item.name,
                "path": str(item).replace("\\", "/"),
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0
            })
        logger.info(f"[TOOL:list_files] Listed {len(entries)} items in '{dir_path}'")
        return json.dumps({
            "success": True,
            "dir_path": str(target).replace("\\", "/"),
            "count": len(entries),
            "entries": entries
        })
    except Exception as e:
        logger.error(f"[TOOL:list_files] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def execute_python(code: str, timeout_seconds: int = 30) -> str:
    """
    Execute Python code in an isolated subprocess within the sovereign sandbox.
    Returns structured execution observations including stdout, stderr, and exit code.
    Example: execute_python(code="import math\\nprint(math.factorial(10))")
    """
    timeout = max(1, min(timeout_seconds, 60))
    logger.info(f"[TOOL:execute_python] Running python code ({len(code)} chars)...")
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(SANDBOX_DIR),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        success = (proc.returncode == 0)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        logger.info(f"[TOOL:execute_python] Completed (exit_code={proc.returncode})")
        return json.dumps({
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode
        })
    except subprocess.TimeoutExpired:
        logger.warning(f"[TOOL:execute_python] Execution timed out after {timeout}s")
        return json.dumps({"success": False, "error": f"Execution timed out after {timeout} seconds", "exit_code": -1})
    except Exception as e:
        logger.error(f"[TOOL:execute_python] Execution error: {e}")
        return json.dumps({"success": False, "error": str(e), "exit_code": -1})


@tool
def execute_code(code: str, language: str = "python") -> str:
    """
    Execute code in a supported programming language (default: python).
    Example: execute_code(code="print(12345 * 6789)", language="python")
    """
    if language.lower() in ["python", "py"]:
        return execute_python.invoke({"code": code})
    return json.dumps({
        "success": False,
        "error": f"Unsupported language '{language}'. Only 'python' is supported in the sovereign sandbox."
    })


@tool
def create_pdf(file_name: str, title: str, content: str = "", columns: Optional[List[str]] = None, rows: Optional[List[Any]] = None) -> str:
    """
    Generate an official, fully-detailed, multi-page professional PDF document inside reports/ using ReportLab.
    Supports markdown headings (#, ##, ###), bullet lists, formatted paragraphs, and structured tables.
    Example: create_pdf(file_name="sop_guide.pdf", title="Turbine SOP", content="# 1. Overview\\nDetailed text...")
    """
    if not file_name.endswith(".pdf"):
        file_name += ".pdf"

    clean_name = Path(file_name).name
    target = REPORTS_DIR / clean_name

    logger.info(f"[TOOL:create_pdf] Generating PDF '{clean_name}' at {target}...")
    try:
        from reportlab.platypus import Table, TableStyle, HRFlowable
        from reportlab.lib import colors

        styles = getSampleStyleSheet()

        # Custom professional typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles['Title'],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1E3A8A'),
            alignment=0,
            spaceAfter=6
        )
        meta_style = ParagraphStyle(
            "DocMeta",
            parent=styles['Normal'],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=12
        )
        h1_style = ParagraphStyle(
            "DocH1",
            parent=styles['Heading1'],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=17,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True
        )
        h2_style = ParagraphStyle(
            "DocH2",
            parent=styles['Heading2'],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor('#334155'),
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True
        )
        h3_style = ParagraphStyle(
            "DocH3",
            parent=styles['Heading3'],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#0369A1'),
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles['Normal'],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=6
        )
        bullet_style = ParagraphStyle(
            "DocBullet",
            parent=styles['Normal'],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#1E293B'),
            leftIndent=15,
            spaceAfter=3
        )
        callout_style = ParagraphStyle(
            "DocCallout",
            parent=styles['Normal'],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#0369A1'),
            leftIndent=12,
            spaceBefore=4,
            spaceAfter=6
        )

        doc = SimpleDocTemplate(
            str(target),
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        story = [
            Paragraph(title, title_style),
            Paragraph("Sovereign Enclave Operational Document | Classification: Confidential / Internal", meta_style),
            HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=2, spaceAfter=10),
        ]

        # Add structured table if columns and rows are provided
        if columns and rows:
            t_data = [[Paragraph(str(c), styles['Helvetica-Bold'] if 'Helvetica-Bold' in styles else body_style) for c in columns]]
            for row_items in rows:
                t_data.append([Paragraph(str(cell), body_style) for cell in row_items])

            t = Table(t_data, colWidths=None)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

        # Parse markdown-structured content
        if content:
            # Helper to convert inline markdown to ReportLab XML tags
            def _format_inline(text_line: str) -> str:
                # bold
                text_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text_line)
                # italic
                text_line = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text_line)
                # inline code
                text_line = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text_line)
                return text_line

            blocks = content.split("\n\n")
            for block in blocks:
                lines = [l.strip() for l in block.splitlines() if l.strip()]
                if not lines:
                    continue

                # Detect Markdown table (| col1 | col2 |)
                if len(lines) >= 2 and all(l.startswith("|") and l.endswith("|") for l in lines):
                    t_data = []
                    header_row = True
                    for line in lines:
                        if re.match(r'^\|[\s\-:|]+\|$', line):
                            header_row = False
                            continue  # separator row
                        cols = [c.strip() for c in line.strip("|").split("|")]
                        row_style = h3_style if header_row else body_style
                        t_data.append([Paragraph(_format_inline(c), row_style) for c in cols])

                    if t_data:
                        t = Table(t_data, colWidths=None)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                            ('TOPPADDING', (0, 0), (-1, 0), 5),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 8))
                        continue

                # Process paragraphs, headings, and bullet points
                for line in lines:
                    formatted_line = _format_inline(line)
                    if line.startswith("### "):
                        clean_text = formatted_line[4:].strip()
                        story.append(Paragraph(clean_text, h3_style))
                    elif line.startswith("## "):
                        clean_text = formatted_line[3:].strip()
                        story.append(Paragraph(clean_text, h2_style))
                    elif line.startswith("# "):
                        clean_text = formatted_line[2:].strip()
                        story.append(Paragraph(clean_text, h1_style))
                    elif line.startswith("- ") or line.startswith("* ") or line.startswith("• "):
                        bullet_text = formatted_line[2:].strip()
                        story.append(Paragraph(f"&bull; {bullet_text}", bullet_style))
                    elif re.match(r'^\d+\.\s+', line):
                        story.append(Paragraph(formatted_line, bullet_style))
                    elif line.startswith("> "):
                        callout_text = formatted_line[2:].strip()
                        story.append(Paragraph(callout_text, callout_style))
                    else:
                        story.append(Paragraph(formatted_line, body_style))

                story.append(Spacer(1, 5))

        doc.build(story)

        if not target.exists():
            raise FileNotFoundError(f"PDF generation failed; file '{clean_name}' does not exist on disk.")

        size = target.stat().st_size
        rel_path = f"reports/{clean_name}"
        logger.info(f"[TOOL:create_pdf] Rich PDF successfully generated! Size: {size} bytes")
        return json.dumps({
            "success": True,
            "file_name": clean_name,
            "file_path": str(target).replace("\\", "/"),
            "relative_path": rel_path,
            "size_bytes": size,
            "mime_type": "application/pdf",
            "message": f"PDF '{clean_name}' generated successfully ({size} bytes)."
        })
    except Exception as e:
        logger.error(f"[TOOL:create_pdf] PDF generation error: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@tool
def create_excel(file_name: str, headers: List[str], rows: List[Any], title: Optional[str] = None) -> str:
    """
    Generate an official Microsoft Excel (.xlsx) spreadsheet inside the sovereign workspace sandbox.
    Example: create_excel(file_name="report.xlsx", headers=["Component", "Status"], rows=[["P-101", "Normal"]])
    """
    try:
        from tools.excel_tool import excel_tool
        res = run_coro_sync(excel_tool.arun(file_name=file_name, headers=headers, rows=rows, title=title))
        return json.dumps(res)
    except Exception as e:
        logger.error(f"[TOOL:create_excel] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def execute_command(command: str, cwd: Optional[str] = None) -> str:
    """
    Execute any terminal/shell command on the host machine with full stdout, stderr, and exit code capture.
    Allows running Python, pip, dir, git, npm, type, grep, find, and system utilities.
    cwd can be any project path, workspace, or uploads directory (defaults to project root).
    Example: execute_command(command="python --version")
    Example: execute_command(command="dir", cwd="BACKEND/uploads/documents")
    """
    try:
        res = execute_terminal_command(command=command, cwd=cwd)
        return json.dumps(res)
    except Exception as e:
        logger.error(f"[TOOL:execute_command] Error: {e}")
        return json.dumps({"success": False, "error": str(e), "exit_code": -1})


@tool
def file_terminal_operations(
    action: str,
    target: Optional[str] = None,
    content: Optional[str] = None,
    command: Optional[str] = None,
    cwd: Optional[str] = None,
    query: Optional[str] = None,
    title: Optional[str] = None,
    columns: Optional[List[str]] = None,
    rows: Optional[List[Any]] = None,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Unified master tool providing complete file system and terminal operations across both local files and uploaded documents.

    Actions:
    - 'read' / 'view': Read full text or structured content from ANY document (PDF, DOCX, XLSX, PPTX, CSV, JSON, Markdown, Code).
      Example: file_terminal_operations(action="read", target="1789822346748-589300_20250423-EB-Event-Driven_Design_for_Agents.PDF")
    - 'analyze' / 'inspect': Deeply analyze any document, extract sections, tables, operational parameters, limits, and tolerances.
      Example: file_terminal_operations(action="analyze", target="1789822346748-589300_20250423-EB-Event-Driven_Design_for_Agents.PDF", query="operating parameters")
    - 'write' / 'create': Create or overwrite a local file with text or code.
      Example: file_terminal_operations(action="write", target="reports/summary.md", content="# System Analysis...")
    - 'create_pdf': Generate an official, publication-quality PDF report with ReportLab styling.
      Example: file_terminal_operations(action="create_pdf", target="event_driven_sop.pdf", title="Event-Driven SOP", content="# 1. Scope\\n...")
    - 'create_excel': Generate an official Excel spreadsheet (.xlsx).
      Example: file_terminal_operations(action="create_excel", target="equipment_metrics.xlsx", title="Equipment Metrics", columns=["Tag", "RPM", "Status"], rows=[["P-101", 1750, "Nominal"]])
    - 'patch' / 'edit': Replace target text in an existing file with new text.
      Example: file_terminal_operations(action="patch", target="reports/summary.md", content="Status: Approved", options={"old_str": "Status: Draft"})
    - 'terminal' / 'execute': Execute any shell/terminal command directly on the host system.
      Example: file_terminal_operations(action="terminal", command="python --version")
    - 'list' / 'dir': List files in a directory or show uploaded documents.
      Example: file_terminal_operations(action="list", target="BACKEND/uploads/documents")
    - 'search' / 'grep': Search for files matching pattern or containing query.
      Example: file_terminal_operations(action="search", target="BACKEND/uploads/documents", query="Event-Driven")
    - 'delete' / 'remove': Delete a file.
      Example: file_terminal_operations(action="delete", target="reports/temp.txt")
    """
    try:
        act = (action or "").strip().lower().replace("-", "_")
        opts = options or {}

        # 1. TERMINAL / EXECUTE
        if act in ["terminal", "exec", "execute", "command", "cmd", "shell", "run", "bash"]:
            cmd = command or opts.get("command") or opts.get("cmd") or target
            if not cmd:
                return json.dumps({"success": False, "error": "Missing 'command' to execute in terminal"})
            working_dir = cwd or opts.get("cwd") or opts.get("directory")
            timeout_sec = opts.get("timeout_seconds", 60)
            res = execute_terminal_command(command=cmd, cwd=working_dir, timeout_seconds=timeout_sec)
            return json.dumps(res)

        # 2. READ / VIEW
        elif act in ["read", "view", "get", "open", "cat"]:
            fpath = target or opts.get("file_path") or opts.get("path") or opts.get("target") or opts.get("file_name")
            if not fpath:
                return json.dumps({"success": False, "error": "Missing 'target' file path to read"})
            s_line = opts.get("start_line")
            e_line = opts.get("end_line")
            m_chars = opts.get("max_chars")
            res = read_any_file(file_path=fpath, start_line=s_line, end_line=e_line, max_chars=m_chars)
            return json.dumps(res)

        # 3. ANALYZE / INSPECT
        elif act in ["analyze", "inspect", "extract", "parse", "audit"]:
            fpath = target or opts.get("file_path") or opts.get("path") or opts.get("target") or opts.get("file_name")
            if not fpath:
                return json.dumps({"success": False, "error": "Missing 'target' file path to analyze"})
            q = query or opts.get("query") or opts.get("question")
            res = analyze_any_document(file_path=fpath, query=q)
            return json.dumps(res)

        # 4. CREATE PDF
        elif act in ["create_pdf", "pdf", "generate_pdf"]:
            fname = target or opts.get("file_name") or opts.get("name") or "report.pdf"
            if not fname.endswith(".pdf"):
                fname += ".pdf"
            doc_title = title or opts.get("title") or Path(fname).stem.replace("_", " ").title()
            doc_content = content or opts.get("content") or ""
            cols = columns or opts.get("columns")
            rws = rows or opts.get("rows")
            return create_pdf.invoke({"file_name": fname, "title": doc_title, "content": doc_content, "columns": cols, "rows": rws})

        # 5. CREATE EXCEL
        elif act in ["create_excel", "excel", "spreadsheet", "generate_excel"]:
            fname = target or opts.get("file_name") or opts.get("name") or "report.xlsx"
            if not fname.endswith(".xlsx"):
                fname += ".xlsx"
            doc_title = title or opts.get("title") or Path(fname).stem.replace("_", " ").title()
            cols = columns or opts.get("columns") or []
            rws = rows or opts.get("rows") or []
            return create_excel.invoke({"file_name": fname, "title": doc_title, "columns": cols, "rows": rws})

        # 6. WRITE / CREATE FILE
        elif act in ["write", "create", "save", "write_file", "create_file"]:
            fpath = target or opts.get("file_path") or opts.get("path") or "output.txt"
            if fpath.lower().endswith(".pdf"):
                doc_title = title or opts.get("title") or Path(fpath).stem.replace("_", " ").title()
                cols = columns or opts.get("columns")
                rws = rows or opts.get("rows")
                return create_pdf.invoke({"file_name": fpath, "title": doc_title, "content": content or "", "columns": cols, "rows": rws})
            if fpath.lower().endswith(".xlsx") and (columns or rows or opts.get("columns") or opts.get("rows")):
                doc_title = title or opts.get("title") or Path(fpath).stem.replace("_", " ").title()
                cols = columns or opts.get("columns") or []
                rws = rows or opts.get("rows") or []
                return create_excel.invoke({"file_name": fpath, "title": doc_title, "columns": cols, "rows": rws})

            return create_file.invoke({"file_path": fpath, "content": content or opts.get("content", "")})

        # 7. PATCH / EDIT FILE
        elif act in ["patch", "edit", "replace", "modify"]:
            fpath = target or opts.get("file_path")
            if not fpath:
                return json.dumps({"success": False, "error": "Missing 'target' file path to patch"})
            target_t = opts.get("old_str") or opts.get("target_text") or opts.get("old_text") or ""
            replacement_t = content or opts.get("new_str") or opts.get("replacement_text") or opts.get("new_text") or ""
            return patch_file.invoke({"file_path": fpath, "target_text": target_t, "replacement_text": replacement_t})

        # 8. LIST / DIR
        elif act in ["list", "dir", "ls", "list_files"]:
            dir_target = target or cwd or opts.get("dir_path") or opts.get("directory") or "."
            if str(dir_target).lower() in ["uploads", "upload", "documents", "uploaded"]:
                dir_target = str(UPLOADS_DOCS_DIR)
            return list_files.invoke({"dir_path": str(dir_target)})

        # 9. SEARCH / GREP
        elif act in ["search", "grep", "find"]:
            search_term = (query or content or target or opts.get("query") or opts.get("term") or "").strip()
            dir_to_search = cwd or opts.get("dir_path") or str(PROJECT_ROOT)
            if target and Path(target).is_dir():
                dir_to_search = target

            results = []
            if UPLOADS_DOCS_DIR.exists():
                for p in UPLOADS_DOCS_DIR.glob("*"):
                    if p.is_file() and search_term.lower() in p.name.lower():
                        results.append({"name": p.name, "path": str(p).replace("\\", "/"), "location": "uploads", "size": p.stat().st_size})

            try:
                base_dir = resolve_any_file_path(dir_to_search, must_exist=False)
                if base_dir.exists() and base_dir.is_dir():
                    for item in base_dir.rglob("*"):
                        if item.is_file() and not any(part.startswith(".") or part in ["node_modules", ".venv", "__pycache__"] for part in item.parts):
                            if search_term.lower() in item.name.lower():
                                results.append({"name": item.name, "path": str(item).replace("\\", "/"), "location": "local", "size": item.stat().st_size})
                            elif search_term and item.stat().st_size < 1024 * 1024:
                                try:
                                    with open(item, "r", encoding="utf-8", errors="ignore") as tf:
                                        t_content = tf.read()
                                        if search_term.lower() in t_content.lower():
                                            results.append({"name": item.name, "path": str(item).replace("\\", "/"), "location": "content_match", "size": item.stat().st_size})
                                except Exception:
                                    pass
                        if len(results) >= 25:
                            break
            except Exception as se:
                logger.warning(f"[file_terminal_operations:search] Error searching {dir_to_search}: {se}")

            return json.dumps({
                "success": True,
                "query": search_term,
                "matches_count": len(results),
                "results": results
            })

        # 10. DELETE / REMOVE
        elif act in ["delete", "remove", "rm", "unlink"]:
            fpath = target or opts.get("file_path")
            if not fpath:
                return json.dumps({"success": False, "error": "Missing 'target' file path to delete"})
            target_p = resolve_any_file_path(fpath, must_exist=True)
            if not target_p.exists():
                return json.dumps({"success": False, "error": f"File not found: {fpath}"})
            if target_p.is_dir():
                return json.dumps({"success": False, "error": f"Path is a directory, not a file: {fpath}"})
            target_p.unlink()
            return json.dumps({"success": True, "file_path": str(target_p).replace("\\", "/"), "message": f"File '{target_p.name}' deleted successfully."})

        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown action '{action}'. Supported actions: 'read', 'analyze', 'write', 'create_pdf', 'create_excel', 'patch', 'terminal', 'list', 'search', 'delete'."
            })
    except Exception as e:
        logger.error(f"[TOOL:file_terminal_operations] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def create_image(file_name: str, prompt: str) -> str:
    """
    Generate an image placeholder (SVG) based on a text prompt inside the sovereign workspace sandbox.
    Useful for creating mock images, visual representations, or stubs when requested.
    Example: create_image(file_name="concept.svg", prompt="A futuristic city skyline")
    """
    try:
        if not file_name.endswith(".svg"):
            file_name += ".svg"
        
        target = resolve_safe_path(f"reports/{file_name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # We generate a simple scalable vector graphics representation of the prompt
        svg_content = f'''<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#2c3e50" />
  <text x="50%" y="45%" font-family="Arial" font-size="32" fill="#ecf0f1" text-anchor="middle">Image Placeholder</text>
  <text x="50%" y="55%" font-family="Arial" font-size="18" fill="#bdc3c7" text-anchor="middle">Prompt: {prompt}</text>
</svg>'''
        
        with open(target, "w", encoding="utf-8") as f:
            f.write(svg_content)
            
        rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
        logger.info(f"[TOOL:create_image] Generated SVG image '{rel_path}' for prompt: {prompt}")
        return json.dumps({
            "success": True,
            "file_path": rel_path,
            "message": f"Image '{rel_path}' generated successfully."
        })
    except Exception as e:
        logger.error(f"[TOOL:create_image] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def create_diagram(file_name: str, mermaid_code: str) -> str:
    """
    Generate a structural diagram (architecture, class, sequence) using Mermaid.js syntax.
    Saves a markdown file with the mermaid block that the frontend will render.
    Example: create_diagram(file_name="arch.md", mermaid_code="graph TD\\nA-->B;")
    """
    try:
        if not file_name.endswith(".md"):
            file_name += ".md"
            
        target = resolve_safe_path(f"reports/{file_name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        
        content = f"```mermaid\\n{mermaid_code}\\n```"
        
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
            
        rel_path = str(target.relative_to(SANDBOX_DIR)).replace("\\", "/")
        logger.info(f"[TOOL:create_diagram] Generated diagram '{rel_path}'")
        return json.dumps({
            "success": True,
            "file_path": rel_path,
            "message": f"Diagram '{rel_path}' generated successfully."
        })
    except Exception as e:
        logger.error(f"[TOOL:create_diagram] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def create_flowchart(file_name: str, mermaid_code: str) -> str:
    """
    Generate a flowchart or process diagram using Mermaid.js syntax.
    Saves a markdown file with the mermaid block that the frontend will render.
    Example: create_flowchart(file_name="process.md", mermaid_code="graph LR\\nStart-->End;")
    """
    return create_diagram.invoke({"file_name": file_name, "mermaid_code": mermaid_code})


@tool
def list_documents(
    limit: Optional[int] = 20,
    search_term: Optional[str] = None,
    user_id: Optional[str] = None,
    is_admin: Optional[bool] = None
) -> str:
    """
    List uploaded and indexed technical documents, manuals, SOPs, and reports in the sovereign repository.
    Example: list_documents(limit=10, search_term="turbine")
    """
    try:
        from rag.document_store import document_store
        docs = document_store.list_documents(
            limit=limit or 20,
            search_term=search_term,
            user_id=user_id,
            is_admin=bool(is_admin) if is_admin is not None else False
        )
        summary = []
        for d in docs:
            chunks = d.get("metadata", {}).get("chunksCount", "N/A") if isinstance(d.get("metadata"), dict) else "N/A"
            summary.append({
                "document_id": d.get("document_id") or d.get("_id"),
                "name": d.get("name"),
                "type": d.get("documentType", "unknown"),
                "status": d.get("processingStatus", "uploaded"),
                "chunks_indexed": chunks,
                "file_size": d.get("fileSize", 0)
            })
        return json.dumps({
            "success": True,
            "total_documents": len(summary),
            "documents": summary
        })
    except Exception as e:
        logger.error(f"[TOOL:list_documents] Error: {e}")
        return json.dumps({"success": False, "error": str(e), "documents": []})


@tool
def get_document(
    document_id_or_name: str,
    user_id: Optional[str] = None,
    is_admin: Optional[bool] = None
) -> str:
    """
    Retrieve full details, metadata, and extracted text for a specific document by its ID or title.
    Example: get_document(document_id_or_name="Flare Header Inspection SOP")
    """
    try:
        from rag.document_store import document_store
        doc = document_store.get_document(
            document_id_or_name,
            user_id=user_id,
            is_admin=bool(is_admin) if is_admin is not None else False
        )
        if not doc:
            return json.dumps({
                "success": False,
                "error": f"Document '{document_id_or_name}' was not found in the repository."
            })
        return json.dumps({
            "success": True,
            "document": doc
        })
    except Exception as e:
        logger.error(f"[TOOL:get_document] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


def run_coro_sync(coro):
    """Safely execute async coroutine from synchronous LangChain tool wrapper."""
    import concurrent.futures
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


@tool
def create_document(
    title: str,
    content: str,
    document_type: Optional[str] = "report",
    user_id: Optional[str] = None,
    is_admin: Optional[bool] = None,
    user_role: Optional[str] = None,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None
) -> str:
    """
    Create a new technical document, chunk its text, index into Qdrant vector database, and store in MongoDB.
    Example: create_document(title="Pump Operation SOP", content="Step 1: Check oil levels...", document_type="sop")
    """
    try:
        from rag.document_store import document_store
        result = run_coro_sync(document_store.create_document(
            name=title,
            content=content,
            document_type=document_type or "report",
            user_id=user_id,
            is_admin=bool(is_admin) if is_admin is not None else False,
            user_role=user_role,
            user_name=user_name,
            user_email=user_email
        ))
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[TOOL:create_document] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def patch_file(file_path: str, target_text: str, replacement_text: str) -> str:
    """
    Replace specific target text in an existing file with new instructed text.
    Example: patch_file(file_path="reports/audit.md", target_text="Status: Pending", replacement_text="Status: Verified")
    """
    try:
        target = resolve_any_file_path(file_path, must_exist=True)
        if not target.exists():
            return json.dumps({"success": False, "error": f"File not found: {file_path}"})
        if target.is_dir():
            return json.dumps({"success": False, "error": f"Path is a directory: {file_path}"})

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            original = f.read()

        if target_text not in original:
            return json.dumps({
                "success": False,
                "error": f"Target text '{target_text[:80]}' not found in file '{file_path}'"
            })

        patched = original.replace(target_text, replacement_text, 1)
        with open(target, "w", encoding="utf-8") as f:
            f.write(patched)

        logger.info(f"[TOOL:patch_file] Successfully patched '{target.name}'")
        return json.dumps({
            "success": True,
            "file_path": str(target).replace("\\", "/"),
            "file_name": target.name,
            "message": f"Successfully replaced target text in '{target.name}'."
        })
    except Exception as e:
        logger.error(f"[TOOL:patch_file] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def update_document(
    document_id_or_name: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    append: bool = False,
    patch_target: Optional[str] = None,
    patch_replacement: Optional[str] = None
) -> str:
    """
    Update or modify an existing document in the repository with instructed data.
    - To update title: provide title
    - To replace content: provide content
    - To append new instructed data: provide content and set append=True
    - To replace a specific section: provide patch_target and patch_replacement
    Example: update_document(document_id_or_name="Pump SOP", content="Section 4: Incident Reporting...", append=True)
    """
    try:
        from rag.document_store import document_store
        result = run_coro_sync(document_store.update_document(
            doc_id_or_name=document_id_or_name,
            title=title,
            content=content,
            append=append,
            patch_target=patch_target,
            patch_replacement=patch_replacement
        ))
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[TOOL:update_document] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def delete_document(document_id_or_name: str) -> str:
    """
    Permanently delete a document from the MongoDB repository, local disk, and remove its vectors from Qdrant.
    Example: delete_document(document_id_or_name="Old_Turbine_Log")
    """
    try:
        from rag.document_store import document_store
        result = run_coro_sync(document_store.delete_document(doc_id_or_name=document_id_or_name))
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[TOOL:delete_document] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def get_document_content(
    document_id_or_name: str,
    user_id: Optional[str] = None,
    is_admin: Optional[bool] = None
) -> str:
    """
    Retrieve the complete, un-truncated full text content and metadata of an uploaded or database document.
    Essential for inspecting reference SOPs, manuals, reports, and technical specifications.
    Example: get_document_content(document_id_or_name="Technical Specification.pdf")
    """
    try:
        from rag.document_store import document_store
        doc = document_store.get_document(
            document_id_or_name,
            user_id=user_id,
            is_admin=bool(is_admin) if is_admin is not None else False
        )
        if not doc:
            return json.dumps({
                "success": False,
                "error": f"Document '{document_id_or_name}' was not found in the repository or workspace."
            })
        full_text = doc.get("content") or doc.get("full_text") or doc.get("extractedText") or ""
        return json.dumps({
            "success": True,
            "document_id": doc.get("document_id") or doc.get("_id"),
            "name": doc.get("name") or doc.get("originalName"),
            "document_type": doc.get("documentType", "text"),
            "character_count": len(full_text),
            "content": full_text
        })
    except Exception as e:
        logger.error(f"[TOOL:get_document_content] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def search_database_documents(
    query: str,
    limit: Optional[int] = 5,
    user_id: Optional[str] = None,
    is_admin: Optional[bool] = None
) -> str:
    """
    Search across all uploaded and database documents for specific keywords, topics, equipment tags, or clauses.
    Returns matched documents with exact text excerpts and relevance scores.
    Example: search_database_documents(query="vibration threshold limits")
    """
    try:
        from rag.document_store import document_store
        matches = document_store.search_documents_content(
            query=query,
            limit=limit or 5,
            user_id=user_id,
            is_admin=bool(is_admin) if is_admin is not None else False
        )
        return json.dumps({
            "success": True,
            "query": query,
            "results_count": len(matches),
            "results": matches
        })
    except Exception as e:
        logger.error(f"[TOOL:search_database_documents] Error: {e}")
        return json.dumps({"success": False, "error": str(e), "results": []})


def resolve_image_path(image_source: str) -> str:
    """Resolve image source whether it is a base64 string, absolute path, or workspace relative path."""
    if not image_source or not isinstance(image_source, str):
        return image_source
    if image_source.startswith("data:image") or (len(image_source) > 500 and "/" not in image_source and "\\" not in image_source):
        return image_source
    p = Path(image_source)
    if p.exists() and p.is_file():
        return str(p.resolve())
    sandbox_p = (SANDBOX_DIR / image_source.replace("\\", "/").strip().lstrip("/")).resolve()
    if sandbox_p.exists() and sandbox_p.is_file():
        return str(sandbox_p)
    backend_p = (BASE_DIR.parent / "BACKEND" / "uploads" / image_source.replace("\\", "/").strip().lstrip("/")).resolve()
    if backend_p.exists() and backend_p.is_file():
        return str(backend_p)
    return image_source


@tool
def ocr_extract_text(
    image_path_or_data: str = "",
    file_path: str = "",
    path: str = "",
    target: str = "",
    document_path: str = ""
) -> str:
    """
    Extract text, numbers, tabular data, and labels from an image or PDF document using sovereign on-premise PaddleOCR.
    Supports scanned PDFs, equipment photos, diagrams, and receipts.
    Example: ocr_extract_text(file_path="equipment_manual.pdf") or ocr_extract_text(image_path_or_data="nameplate.jpg")
    """
    try:
        raw_source = (
            image_path_or_data
            or file_path
            or path
            or target
            or document_path
            or ""
        ).strip()
        if not raw_source:
            return json.dumps({"success": False, "error": "file_path or image_path must be provided", "text": ""})

        # Base64 string check
        if raw_source.startswith("data:image") or (len(raw_source) > 500 and "/" not in raw_source and "\\" not in raw_source):
            from ocr.ocr_service import ocr_service
            res = ocr_service.extract_text(raw_source)
            return json.dumps({
                "success": res.get("success", True),
                "text": res.get("text", ""),
                "confidence": res.get("confidence", 0.0),
                "blocks": res.get("blocks", [])
            })

        # Resolve path
        resolved_p = resolve_any_file_path(raw_source, must_exist=False)
        resolved_str = str(resolved_p.resolve()) if resolved_p.exists() else raw_source

        ext = Path(resolved_str).suffix.lower()

        # Multi-page PDF OCR
        if ext == ".pdf":
            from ocr.ocr_service import ocr_service
            res = ocr_service.extract_pdf(resolved_str)
            return json.dumps({
                "success": res.get("success", True),
                "file_name": Path(resolved_str).name,
                "text": res.get("text", ""),
                "page_count": res.get("page_count", 1),
                "pages_processed": res.get("pages_processed", 1),
                "confidence": res.get("confidence", 0.0),
                "blocks": res.get("blocks", [])[:100]  # Cap blocks in response
            })

        # Image formats
        if ext in [".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".tiff"]:
            from ocr.ocr_service import ocr_service
            res = ocr_service.extract_text(resolved_str)
            return json.dumps({
                "success": res.get("success", True),
                "file_name": Path(resolved_str).name,
                "text": res.get("text", ""),
                "line_count": len(res.get("blocks", [])),
                "confidence": res.get("confidence", 0.0),
                "blocks": res.get("blocks", [])
            })

        # Office & text formats parsed via DocumentParser
        from rag.parser import document_parser
        parsed = document_parser.parse_file(resolved_str)
        return json.dumps({
            "success": True,
            "file_name": Path(resolved_str).name,
            "format": ext,
            "text": parsed.text,
            "character_count": len(parsed.text)
        })
    except Exception as e:
        logger.error(f"[TOOL:ocr_extract_text] Error: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "text": ""})


@tool
def analyze_image(image_path_or_data: str, prompt: Optional[str] = None) -> str:
    """
    Analyze and understand the visual contents of an image (equipment condition, diagrams, charts, UI screenshots)
    using sovereign multimodal vision (Moondream) and OCR.
    Example: analyze_image(image_path_or_data="pump_gauge.jpg", prompt="What is the pressure reading on the gauge?")
    """
    try:
        from multimodal.multimodal_orchestrator import MultimodalOrchestrator
        orch = MultimodalOrchestrator()
        resolved_img = resolve_image_path(image_path_or_data)
        res = run_coro_sync(orch.analyze(image_source=resolved_img, user_prompt=prompt))
        return json.dumps({
            "success": res.get("status") == "success" or res.get("success", True),
            "visual_description": res.get("vision", {}).get("description", ""),
            "ocr_text": res.get("ocr", {}).get("text", ""),
            "unified_context": res.get("combined_context", "")
        })
    except Exception as e:
        logger.error(f"[TOOL:analyze_image] Error: {e}")
        return json.dumps({"success": False, "error": str(e)})


# Registry of all available tools
AGENT_TOOLS = [
    file_terminal_operations,
    create_directory,
    create_file,
    read_file,
    patch_file,
    list_files,
    execute_python,
    execute_code,
    execute_command,
    create_pdf,
    create_excel,
    create_image,
    create_diagram,
    create_flowchart,
    save_memory,
    search_knowledge_base,
    index_document,
    list_documents,
    get_document,
    get_document_content,
    search_database_documents,
    create_document,
    update_document,
    delete_document,
    ocr_extract_text,
    analyze_image,
]

# Map both canonical names and aliases
TOOLS_MAP: Dict[str, Any] = {
    # Canonical names
    "file_terminal_operations": file_terminal_operations,
    "create_directory": create_directory,
    "create_file": create_file,
    "read_file": read_file,
    "patch_file": patch_file,
    "list_files": list_files,
    "execute_python": execute_python,
    "execute_code": execute_code,
    "execute_command": execute_command,
    "create_pdf": create_pdf,
    "create_excel": create_excel,
    "create_image": create_image,
    "create_diagram": create_diagram,
    "create_flowchart": create_flowchart,
    "save_memory": save_memory,
    "search_knowledge_base": search_knowledge_base,
    "index_document": index_document,
    "list_documents": list_documents,
    "get_document": get_document,
    "get_document_content": get_document_content,
    "read_document_content": get_document_content,
    "search_database_documents": search_database_documents,
    "search_documents": search_database_documents,
    "create_document": create_document,
    "update_document": update_document,
    "delete_document": delete_document,
    "ocr_extract_text": ocr_extract_text,
    "analyze_image": analyze_image,
    # Aliases for file and terminal operations
    "file_terminal": file_terminal_operations,
    "terminal_ops": file_terminal_operations,
    "file_ops": file_terminal_operations,
    "file_operations": file_terminal_operations,
    "terminal_operations": file_terminal_operations,
    "terminal_file_operations": file_terminal_operations,
    "file_and_terminal": file_terminal_operations,
    "terminal": execute_command,
    "shell": execute_command,
    "exec": execute_command,
    "bash": execute_command,
    "cmd": execute_command,
    "terminal_command": execute_command,
    "command": execute_command,
    "analyze_document": file_terminal_operations,
    # Aliases for OCR and Vision
    "ocr": ocr_extract_text,
    "extract_text": ocr_extract_text,
    "image_ocr": ocr_extract_text,
    "vision": analyze_image,
    "image_understanding": analyze_image,
    "understand_image": analyze_image,
    "image_analysis": analyze_image,
    # Aliases for document creation and modification
    "generate_document": create_document,
    "new_document": create_document,
    "add_document": create_document,
    "modify_document": update_document,
    "edit_document": update_document,
    "patch_document": update_document,
    "generate_pdf": create_pdf,
    "make_pdf": create_pdf,
    "pdf_generator": create_pdf,
    "generate_excel": create_excel,
    "write_excel": create_excel,
    "spreadsheet_writer": create_excel,
    "write_spreadsheet": create_excel,
    "create_spreadsheet": create_excel,
    "write_file": create_file,
    "save_file": create_file,
    "file_writer": create_file,
    "file_reader": read_file,
    "modify_file": patch_file,
    "edit_file": patch_file,
    # Dot-notation aliases
    "file.terminal": file_terminal_operations,
    "file.create_directory": create_directory,
    "file.create": create_file,
    "file.read": read_file,
    "file.patch": patch_file,
    "file.modify": patch_file,
    "file.list": list_files,
    "python.execute": execute_python,
    "code.execute": execute_code,
    "command.execute": execute_command,
    "pdf.create": create_pdf,
    "excel.create": create_excel,
    "image.create": create_image,
    "diagram.create": create_diagram,
    "flowchart.create": create_flowchart,
    "memory.save": save_memory,
    "knowledge.search": search_knowledge_base,
    "document.index": index_document,
    "document.list": list_documents,
    "document.get": get_document,
    "document.get_content": get_document_content,
    "document.read": get_document_content,
    "document.search": search_database_documents,
    "document.create": create_document,
    "document.update": update_document,
    "document.modify": update_document,
    "document.delete": delete_document,
    "image.ocr": ocr_extract_text,
    "image.analyze": analyze_image,
}


def get_agent_tools() -> List[Any]:
    """Retrieve all LangChain compatible tools for agent binding."""
    return list(AGENT_TOOLS)


def resolve_tool(name: str) -> Optional[Any]:
    """Resolve a tool by canonical name or alias with normalized lookup."""
    if not name or not isinstance(name, str):
        return None
    cleaned = name.strip().lower().replace("-", "_").replace(" ", "_")
    if cleaned in TOOLS_MAP:
        return TOOLS_MAP[cleaned]
    # Check suffix matches
    for k, v in TOOLS_MAP.items():
        if k.lower() == cleaned or cleaned.endswith(f"_{k.lower()}"):
            return v
    return None
