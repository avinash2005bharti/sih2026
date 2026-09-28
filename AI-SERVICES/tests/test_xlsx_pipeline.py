import pytest
import asyncio
from pathlib import Path
from tools.spreadsheet_tool import SpreadsheetCreatorTool
from tools.validators.xlsx_validator import validate_xlsx_artifact
import openpyxl

def test_xlsx_creation_and_validation():
    async def _run():
        tool = SpreadsheetCreatorTool()
        headers = ["Equipment Tag", "Subsystem", "Baseline Vibration", "Current Vibration", "Status"]
        rows = [
            ["FAN-01", "Motor Drive End", 1.2, 1.4, "Optimal"],
            ["FAN-02", "Impeller Shaft", 1.5, 3.8, "Warning"],
            ["FAN-03", "Non-Drive Bearing", 1.1, 1.2, "Optimal"]
        ]

        res = await tool.execute(
            title="Vibration Tracker",
            headers=headers,
            rows=rows,
            filename="test_vibration_tracker.xlsx",
            summary_formula="=COUNTA(A2:A4)"
        )

        assert res["status"] == "success"
        xlsx_path = res["file_path"]
        assert Path(xlsx_path).exists()

        val = validate_xlsx_artifact(xlsx_path)
        assert val["valid"] is True
        assert val["metadata"]["row_count"] >= 4
        assert val["metadata"]["formula_count"] >= 1
    asyncio.run(_run())

def test_xlsx_validator_catches_formula_errors(tmp_path):
    bad_xlsx = tmp_path / "broken_formulas.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Tag", "Reading"])
    ws.append(["T-1", "#REF!"])
    wb.save(str(bad_xlsx))

    val = validate_xlsx_artifact(str(bad_xlsx))
    assert val["valid"] is False
    assert any("#REF!" in issue for issue in val["issues"])
