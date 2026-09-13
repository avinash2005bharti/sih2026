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

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".log", ".json", ".csv", ".pdf"}

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

        if ext in [".txt", ".md", ".log"]:
            text = self._parse_text(path)
        elif ext == ".json":
            text = self._parse_json(path)
        elif ext == ".csv":
            text = self._parse_csv(path)
        elif ext == ".pdf":
            text = self._parse_pdf(path)
        else:
            text = self._parse_text(path)

        logger.info(f"Parsed {path.name} ({len(text)} characters, format: {ext})")
        return ParsedDocument(text=text, metadata=metadata)

    def _parse_text(self, path: Path) -> str:
        """Parse plain text / markdown / log file with encoding fallback."""
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
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
            with open(path, "r", encoding="utf-8", errors="replace") as f:
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
        Parse PDF file using pure-python stream text extraction
        or pypdf / pypdf2 if available.
        """
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except ImportError:
            pass

        # Fallback: native regex text extraction from uncompressed PDF streams
        try:
            with open(path, "rb") as f:
                content = f.read().decode("latin-1", errors="ignore")

            # Extract text within BT (begin text) and ET (end text) blocks
            text_blocks = []
            for match in re.finditer(r"BT\s*(.*?)\s*ET", content, re.DOTALL):
                block = match.group(1)
                # Match strings in parentheses (Tj or TJ commands)
                strings = re.findall(r"\((.*?)\)", block)
                if strings:
                    text_blocks.append(" ".join(strings))

            if text_blocks:
                return "\n".join(text_blocks)
        except Exception as e:
            logger.warning(f"PDF stream parsing warning: {e}")

        return f"[PDF Document: {path.name} (binary indexed)]"


document_parser = DocumentParser()
