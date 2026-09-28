import pytest
import asyncio
from pathlib import Path
from tools.document_tool import DocumentCreatorTool
from tools.validators.docx_validator import validate_docx_artifact

def test_docx_creation_and_validation():
    async def _run():
        tool = DocumentCreatorTool()
        sections = [
            {"heading": "Purpose & Scope", "content": "Defines standard operating procedure for boiler blowout."},
            {"heading": "Safety Precautions", "content": "Full thermal suit and PPE required. Verify pressure gauge below 10 bar."},
            {
                "heading": "Step-by-Step Procedure",
                "content": "Follow the sequence precisely:",
                "table_data": [
                    ["Step", "Action", "Verification"],
                    ["1", "Isolate feed valve", "Gauge drops to 0"],
                    ["2", "Open vent 3A", "Audible steam hiss"]
                ]
            }
        ]

        res = await tool.execute(
            title="Boiler Blowout SOP",
            sections=sections,
            filename="test_boiler_sop.docx"
        )

        assert res["status"] == "success"
        docx_path = res["file_path"]
        assert Path(docx_path).exists()

        val = validate_docx_artifact(docx_path, required_headings=["Safety Precautions"])
        assert val["valid"] is True
        assert val["metadata"]["paragraph_count"] >= 3
        assert val["metadata"]["table_count"] >= 1
    asyncio.run(_run())
