from pathlib import Path
from typing import Any, Dict, List, Optional
import openpyxl
from core.logging import logger

ERROR_CELL_VALUES = ["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#NULL!"]

def validate_xlsx_artifact(
    file_path: str,
    required_sheets: Optional[List[str]] = None,
    min_rows: int = 2,
    min_cols: int = 2
) -> Dict[str, Any]:
    """
    Mandatory Excel (.xlsx) Artifact Validator:
    Inspects workbook structure, valid headers, data rows, valid formulas,
    and absence of Excel error values (#REF!, #DIV/0!, etc.).
    """
    path = Path(file_path)
    issues: List[str] = []
    missing_reqs: List[str] = []
    corrections: List[str] = []

    if not path.exists():
        return {
            "valid": False,
            "score": 0,
            "issues": [f"File does not exist: {file_path}"],
            "missing_requirements": ["Excel file generation"],
            "corrections": ["Generate the workbook using openpyxl."]
        }

    try:
        wb = openpyxl.load_workbook(str(path), data_only=False)
    except Exception as e:
        return {
            "valid": False,
            "score": 0,
            "issues": [f"Failed to open Excel workbook: {str(e)}"],
            "missing_requirements": ["Valid XLSX format"],
            "corrections": ["Ensure workbook is saved in standard XLSX format without corruption."]
        }

    sheet_names = wb.sheetnames
    if not sheet_names:
        return {
            "valid": False,
            "score": 0,
            "issues": ["Workbook contains no sheets."],
            "missing_requirements": ["At least one active sheet"],
            "corrections": ["Create at least one worksheet with data."]
        }

    # Check required sheets
    if required_sheets:
        for s in required_sheets:
            if s not in sheet_names:
                issues.append(f"Required worksheet '{s}' was not found.")
                missing_reqs.append(f"Sheet: {s}")
                corrections.append(f"Add sheet '{s}' to workbook.")

    active_sheet = wb.active
    rows = list(active_sheet.iter_rows(values_only=True))

    if len(rows) < min_rows:
        issues.append(f"Sheet '{active_sheet.title}' has {len(rows)} rows; expected at least {min_rows}.")
        missing_reqs.append("Data rows in worksheet")
        corrections.append("Populate rows with structured records.")

    # Header check: locate the header row (first non-empty row with at least min_cols cells, skipping title banners)
    headers = []
    for r in rows:
        candidate = [str(cell).strip() for cell in r if cell is not None and str(cell).strip() != ""]
        if len(candidate) >= min_cols:
            headers = candidate
            break
    if not headers and rows:
        headers = [str(cell).strip() for cell in rows[0] if cell is not None and str(cell).strip() != ""]

    if len(headers) < min_cols:
        issues.append(f"Header row has only {len(headers)} columns; expected at least {min_cols}.")
        missing_reqs.append("Sufficient column headers")
        corrections.append("Define clear column headers (e.g. Asset ID, Status, Severity).")

    # Formula & error values check
    error_count = 0
    formula_count = 0
    for row in rows:
        for val in row:
            if val is not None:
                s_val = str(val).strip()
                if any(err in s_val for err in ERROR_CELL_VALUES):
                    issues.append(f"Detected formula error cell value '{s_val}'.")
                    error_count += 1
                if s_val.startswith("="):
                    formula_count += 1

    score = 100 - (len(issues) * 20)
    score = max(0, min(100, score))
    is_valid = len(issues) == 0

    logger.info(
        f"XLSX VALIDATION | File: {path.name} | Valid: {is_valid} | Score: {score} | "
        f"Rows: {len(rows)} | Formulas: {formula_count} | Issues: {len(issues)}"
    )

    return {
        "valid": is_valid,
        "score": score,
        "issues": issues,
        "missing_requirements": missing_reqs,
        "corrections": corrections,
        "metadata": {
            "sheet_count": len(sheet_names),
            "sheets": sheet_names,
            "row_count": len(rows),
            "col_count": len(headers),
            "formula_count": formula_count
        }
    }
