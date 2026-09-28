import pytest
import asyncio
from pathlib import Path
from tools.pdf_tool import PDFCreatorTool
from tools.validators.pdf_validator import validate_pdf_artifact

def test_pdf_creation_and_positive_validation():
    async def _run():
        tool = PDFCreatorTool()
        sections = [
            {
                "heading": "Executive Summary",
                "content": "This executive summary outlines the critical preventive maintenance conducted on the plant chillers."
            },
            {
                "heading": "Equipment Details",
                "content": "Inspection telemetry on Chiller CH-01 and associated primary coolant pump P-102.",
                "table_data": [
                    ["Unit", "Vibration", "Discharge PSI", "Bearing Temp"],
                    ["CH-01", "2.1 mm/s", "145 PSI", "68°C"],
                    ["P-102", "1.8 mm/s", "120 PSI", "62°C"]
                ]
            },
            {
                "heading": "Inspection Findings & Risks",
                "content": "Risk assessment highlights slight cavitation in impeller casing. Failure risk is moderate with severity rating 6."
            },
            {
                "heading": "Actionable Recommendations",
                "content": "1. Bleed suction line. 2. Verify inlet strainer. 3. Recheck vibration in 72 hours."
            }
        ]

        res = await tool.execute(
            title="Industrial Maintenance Inspection Report",
            sections=sections,
            filename="test_maintenance_report.pdf"
        )

        assert res["status"] == "success"
        pdf_path = res["file_path"]
        assert Path(pdf_path).exists()

        # Artifact Validation Check
        val = validate_pdf_artifact(pdf_path)
        assert val["valid"] is True
        assert val["score"] >= 80
        assert val["metadata"]["page_count"] >= 1
        assert val["metadata"]["total_chars"] > 150
    asyncio.run(_run())

def test_pdf_validation_catches_placeholders(tmp_path):
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    bad_pdf = tmp_path / "bad_report.pdf"
    doc = SimpleDocTemplate(str(bad_pdf))
    styles = getSampleStyleSheet()
    doc.build([Paragraph("Executive Summary [Insert findings here] TODO: check bearings", styles['Normal'])])

    val = validate_pdf_artifact(str(bad_pdf))
    assert val["valid"] is False
    assert any("placeholder" in issue.lower() for issue in val["issues"])
