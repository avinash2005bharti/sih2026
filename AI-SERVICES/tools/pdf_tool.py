import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from tools.base_tool import BaseTool
from tools.validators.pdf_validator import validate_pdf_artifact
from core.config import settings
from core.security import validate_safe_path
from core.logging import logger

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import pypdf

class PDFCreatorTool(BaseTool):
    name: str = "pdf_creator"
    description: str = "Generate a professional industrial inspection or engineering PDF report."
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the report."},
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "content": {"type": "string"},
                        "table_data": {"type": "array"}
                    },
                    "required": ["heading", "content"]
                }
            },
            "filename": {"type": "string", "description": "Output filename (e.g. maintenance_report.pdf)"}
        },
        "required": ["title", "sections"]
    }
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "validation": {"type": "object"}
        }
    }
    permissions: List[str] = ["analyst", "engineer", "operator", "admin"]
    risk_level: str = "low"

    async def arun(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        filename: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return await self.execute(title=title, sections=sections, filename=filename, **kwargs)

    async def execute(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        filename: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        try:
            fname = filename or f"report_{int(time.time())}.pdf"
            if not fname.endswith(".pdf"):
                fname += ".pdf"
            target_path = settings.ARTIFACT_DIR / fname
            safe_path = validate_safe_path(str(target_path))

            doc = SimpleDocTemplate(
                str(safe_path),
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )

            styles = getSampleStyleSheet()
            
            # Custom styled palette
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=22,
                leading=26,
                textColor=colors.HexColor('#0F172A'),
                spaceAfter=12
            )
            subtitle_style = ParagraphStyle(
                'ReportSub',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748B'),
                spaceAfter=15
            )
            h2_style = ParagraphStyle(
                'SectionHeading',
                parent=styles['Heading2'],
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#1E3A8A'),
                spaceBefore=14,
                spaceAfter=6
            )
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#334155'),
                spaceAfter=8
            )

            elements = []
            elements.append(Paragraph(title, title_style))
            elements.append(Paragraph(f"SOVEREIGN ON-PREMISE INDUSTRIAL REPORT | Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

            required_headings_found = []

            for sec in sections:
                heading = sec.get("heading", "Section")
                content = sec.get("content", "")
                table_data = sec.get("table_data", None)

                required_headings_found.append(heading)
                elements.append(Paragraph(heading, h2_style))
                elements.append(Paragraph(content.replace("\n", "<br/>"), body_style))

                if table_data and isinstance(table_data, list) and len(table_data) > 0:
                    # Format table cells with Paragraphs
                    formatted_table = []
                    for row_idx, row in enumerate(table_data):
                        formatted_row = []
                        for cell in row:
                            cell_text = str(cell)
                            c_style = ParagraphStyle('TCell', parent=styles['Normal'], fontSize=9, leading=11)
                            if row_idx == 0:
                                c_style.textColor = colors.whitesmoke
                                c_style.fontName = 'Helvetica-Bold'
                            formatted_row.append(Paragraph(cell_text, c_style))
                        formatted_table.append(formatted_row)

                    t = Table(formatted_table, colWidths=None)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
                    ]))
                    elements.append(Spacer(1, 6))
                    elements.append(t)
                    elements.append(Spacer(1, 10))

                elements.append(Spacer(1, 10))

            doc.build(elements)

            # Mandatory immediate artifact validation!
            validation = validate_pdf_artifact(str(safe_path))

            return {
                "status": "success",
                "file_path": str(safe_path),
                "filename": fname,
                "validation": validation
            }
        except Exception as e:
            logger.error(f"PDF creation error: {e}")
            return {"status": "error", "error": str(e)}

class PDFReaderTool(BaseTool):
    name: str = "pdf_reader"
    description: str = "Extract text, metadata, and page count from a PDF document."
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the PDF file."}
        },
        "required": ["file_path"]
    }
    permissions: List[str] = ["viewer", "analyst", "engineer", "operator", "admin"]
    risk_level: str = "low"

    async def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        try:
            safe_path = validate_safe_path(file_path)
            reader = pypdf.PdfReader(str(safe_path))
            pages_text = [p.extract_text() or "" for p in reader.pages]
            return {
                "status": "success",
                "file_path": str(safe_path),
                "page_count": len(reader.pages),
                "text": "\n--- PAGE BREAK ---\n".join(pages_text)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
