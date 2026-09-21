"""
Multi-format document parser for Sovereign RAG pipeline.
Extracts clean plain text and structural metadata from files:
.txt, .md, .csv, .json, .log, and .pdf.
"""

import os
import re
import json
import csv
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from core.logging import logger


class ParsedDocument:
    """Represents the parsed text and metadata of a source file."""
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata

    def __repr__(self):
        return f"<ParsedDocument source='{self.metadata.get('source')}' length={len(self.text)}>"


class DocumentParser:
    """Extracts text content and metadata from multiple file formats."""

    SUPPORTED_EXTENSIONS = {
        ".txt", ".md", ".log", ".json", ".csv", ".pdf",
        ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
        ".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".tiff",
        ".xml", ".yaml", ".yml", ".rtf"
    }

    def parse_file(self, file_path: str) -> ParsedDocument:
        """Parse file from disk and return ParsedDocument."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: {self.SUPPORTED_EXTENSIONS}")

        stat = path.stat()
        metadata = {
            "source": path.name,
            "file_path": str(path.resolve()),
            "extension": ext,
            "size_bytes": stat.st_size,
            "modified_time": stat.st_mtime
        }

        if ext in [".txt", ".md", ".log", ".rtf", ".xml", ".yaml", ".yml"]:
            text = self._parse_text(path)
        elif ext == ".json":
            text = self._parse_json(path)
        elif ext == ".csv":
            text = self._parse_csv(path)
        elif ext == ".pdf":
            text = self._parse_pdf(path)
        elif ext in [".docx", ".doc"]:
            text = self._parse_docx(path)
        elif ext in [".xlsx", ".xls"]:
            text = self._parse_xlsx(path)
        elif ext in [".pptx", ".ppt"]:
            text = self._parse_pptx(path)
        elif ext in [".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".tiff"]:
            text = self._parse_image(path)
        else:
            text = self._parse_text(path)

        logger.info(f"Parsed {path.name} ({len(text)} characters, format: {ext})")
        return ParsedDocument(text=text, metadata=metadata)

    def _parse_text(self, path: Path) -> str:
        """Parse plain text / markdown / log file with encoding fallback."""
        for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                with open(path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _parse_json(self, path: Path) -> str:
        """Parse JSON file into structured readable text representation."""
        raw = self._parse_text(path)
        try:
            data = json.loads(raw)
            return json.dumps(data, indent=2)
        except Exception:
            return raw

    def _parse_csv(self, path: Path) -> str:
        """Parse CSV file into textual rows."""
        lines = []
        try:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    lines.append(f"Columns: {', '.join(header)}")
                for row_idx, row in enumerate(reader):
                    lines.append(f"Row {row_idx + 1}: {', '.join(row)}")
                    if row_idx >= 500:  # Cap at 500 rows to prevent massive text blocks
                        lines.append("... [Additional CSV rows truncated for RAG indexing]")
                        break
            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"CSV parse error: {e}, falling back to plain text")
            return self._parse_text(path)

    def _parse_pdf(self, path: Path) -> str:
        """
        Parse PDF file using pypdf text extraction, with automatic OCR fallback
        via pypdfium2 + PaddleOCR for scanned or image-based PDF pages.
        """
        extracted_pages = []
        total_pypdf_chars = 0
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for page_idx, page in enumerate(reader.pages):
                page_text = (page.extract_text() or "").strip()
                if page_text:
                    extracted_pages.append(f"--- Page {page_idx + 1} ---\n{page_text}")
                    total_pypdf_chars += len(page_text)
        except Exception as pe:
            logger.warning(f"pypdf extraction error on {path.name}: {pe}")

        num_pages = len(reader.pages) if 'reader' in locals() and hasattr(reader, "pages") else 1
        avg_chars = total_pypdf_chars / max(1, num_pages)

        # If digital text exists and is sufficiently dense (>= 30 chars/page), return it
        if total_pypdf_chars > 60 and avg_chars >= 30:
            return "\n\n".join(extracted_pages).strip()

        # Scanned or image-heavy PDF: Run OCR via pypdfium2 + PaddleOCR
        logger.info(f"PDF {path.name} appears scanned or image-based ({total_pypdf_chars} digital chars, {num_pages} pages). Executing OCR extraction...")
        try:
            import pypdfium2 as pdfium
            from ocr.ocr_service import ocr_service

            doc = pdfium.PdfDocument(str(path))
            ocr_pages = []
            max_pages = min(len(doc), 30)  # Bound to 30 pages to protect memory & CPU
            for idx in range(max_pages):
                page = doc[idx]
                pil_img = page.render(scale=2.0).to_pil()
                res = ocr_service.extract_text(pil_img)
                page_text = res.get("text", "").strip()
                if page_text:
                    ocr_pages.append(f"--- Page {idx + 1} (OCR) ---\n{page_text}")
                elif idx < len(extracted_pages) and extracted_pages[idx].strip():
                    ocr_pages.append(extracted_pages[idx])

            if ocr_pages:
                logger.info(f"OCR extracted {len(ocr_pages)} pages from scanned PDF {path.name}")
                return "\n\n".join(ocr_pages).strip()
        except Exception as ocr_err:
            logger.warning(f"PDF OCR extraction warning on {path.name}: {ocr_err}")

        # Fallback: native regex text extraction from uncompressed PDF streams
        try:
            with open(path, "rb") as f:
                content = f.read().decode("latin-1", errors="ignore")

            text_blocks = []
            for match in re.finditer(r"BT\s*(.*?)\s*ET", content, re.DOTALL):
                block = match.group(1)
                strings = re.findall(r"\((.*?)\)", block)
                if strings:
                    text_blocks.append(" ".join(strings))

            if text_blocks:
                return "\n".join(text_blocks)
        except Exception as e:
            logger.warning(f"PDF stream parsing warning: {e}")

        return "\n\n".join(extracted_pages).strip() if extracted_pages else f"[PDF Document: {path.name}]"

    def _parse_docx(self, path: Path) -> str:
        """Extract text from Word DOCX/DOC files including headings, paragraphs, and tables."""
        ext = path.suffix.lower()
        if ext == ".docx":
            try:
                import docx
                doc = docx.Document(str(path))
                sections = []
                for p in doc.paragraphs:
                    t = p.text.strip()
                    if t:
                        sections.append(t)
                for table in doc.tables:
                    table_rows = []
                    for row in table.rows:
                        row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                        if row_text and row_text not in table_rows:
                            table_rows.append(row_text)
                    if table_rows:
                        sections.append("\n".join(table_rows))
                return "\n\n".join(sections)
            except Exception as e:
                logger.warning(f"DOCX parse error on {path.name}: {e}")

        # Fallback for .doc or corrupted docx: extract printable text strings
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
            # Extract readable ascii/utf-8 sequences
            printable_chunks = re.findall(rb'[\x20-\x7E\r\n\t]{4,}', raw_bytes)
            extracted = "\n".join(c.decode("ascii", errors="ignore").strip() for c in printable_chunks if len(c.strip()) > 3)
            if extracted and len(extracted) > 100:
                return extracted
        except Exception:
            pass

        return self._parse_text(path)

    def _parse_xlsx(self, path: Path) -> str:
        """Extract textual and tabular content from Excel spreadsheets (.xlsx, .xls)."""
        ext = path.suffix.lower()

        # 1. Try openpyxl for .xlsx
        if ext == ".xlsx":
            try:
                import openpyxl
                wb = openpyxl.load_workbook(str(path), data_only=True)
                lines = []
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    lines.append(f"=== Sheet: {sheet} ===")
                    for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
                        if row_idx >= 500:
                            lines.append("... [Additional rows truncated]")
                            break
                        row_vals = [str(c).strip() for c in row if c is not None and str(c).strip()]
                        if row_vals:
                            lines.append(" | ".join(row_vals))
                if lines:
                    return "\n".join(lines)
            except Exception as e:
                logger.warning(f"openpyxl parse error on {path.name}: {e}")

        # 2. Try pandas for .xls or fallback
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(str(path))
            lines = []
            for sheet_name in excel_file.sheet_names:
                lines.append(f"=== Sheet: {sheet_name} ===")
                df = excel_file.parse(sheet_name)
                # Cap dataframe rows
                preview_df = df.head(500).dropna(how="all")
                if not preview_df.empty:
                    header = " | ".join([str(col) for col in preview_df.columns])
                    lines.append(f"Columns: {header}")
                    for _, row in preview_df.iterrows():
                        row_vals = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip()]
                        if row_vals:
                            lines.append(" | ".join(row_vals))
            if lines:
                return "\n".join(lines)
        except Exception as pe:
            logger.warning(f"pandas Excel parse error on {path.name}: {pe}")

        return self._parse_text(path)

    def _parse_pptx(self, path: Path) -> str:
        """Extract text from PowerPoint presentations (.pptx, .ppt) including shapes, tables, and notes."""
        ext = path.suffix.lower()
        if ext == ".pptx":
            try:
                from pptx import Presentation
                prs = Presentation(str(path))
                lines = []
                for idx, slide in enumerate(prs.slides):
                    lines.append(f"=== Slide {idx + 1} ===")
                    # Extract text from shapes
                    for shape in slide.shapes:
                        # Standard text frame
                        if hasattr(shape, "has_text_frame") and shape.has_text_frame:
                            for p in shape.text_frame.paragraphs:
                                if p.text and p.text.strip():
                                    lines.append(p.text.strip())
                        # Tables in slide
                        if hasattr(shape, "has_table") and shape.has_table:
                            for row in shape.table.rows:
                                row_vals = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                                if row_vals:
                                    lines.append(" | ".join(row_vals))
                        # Group shapes
                        if hasattr(shape, "shapes"):
                            for sub_shape in shape.shapes:
                                if hasattr(sub_shape, "has_text_frame") and sub_shape.has_text_frame:
                                    for p in sub_shape.text_frame.paragraphs:
                                        if p.text and p.text.strip():
                                            lines.append(p.text.strip())
                    # Slide notes
                    if hasattr(slide, "has_notes_slide") and slide.has_notes_slide:
                        notes_frame = getattr(slide.notes_slide, "notes_text_frame", None)
                        if notes_frame and notes_frame.text and notes_frame.text.strip():
                            lines.append(f"[Slide Notes]: {notes_frame.text.strip()}")
                return "\n".join(lines)
            except Exception as e:
                logger.warning(f"PPTX parse error on {path.name}: {e}")

        # Fallback for .ppt or corrupted files: extract printable text strings
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
            printable_chunks = re.findall(rb'[\x20-\x7E\r\n\t]{4,}', raw_bytes)
            extracted = "\n".join(c.decode("ascii", errors="ignore").strip() for c in printable_chunks if len(c.strip()) > 3)
            if extracted and len(extracted) > 100:
                return extracted
        except Exception:
            pass

        return self._parse_text(path)

    def _parse_image(self, path: Path) -> str:
        """Extract text from images using local PaddleOCR."""
        try:
            from ocr.ocr_service import ocr_service
            res = ocr_service.extract_text(str(path))
            text = res.get("text", "").strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Image OCR error on {path.name}: {e}")
        return f"[Image Document: {path.name}]"


document_parser = DocumentParser()
