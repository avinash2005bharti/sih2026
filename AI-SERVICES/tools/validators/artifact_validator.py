"""
Unified Artifact File Generation Validator.
SIH 26117 — Sovereign On-Premise Agentic AI Workbench.

Validates: PDF, DOCX, XLSX, CSV
Pipeline:
file exists -> file is readable -> expected content exists -> content is relevant -> basic structure validation -> return result
"""

import os
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.logging import logger

DUMMY_PLACEHOLDERS = [
    "lorem ipsum",
    "placeholder",
    "sample text",
    "todo: add content",
    "asdf",
    "test test test"
]


def validate_csv(file_path: str, min_rows: int = 2, min_cols: int = 2) -> Dict[str, Any]:
    issues = []
    rows = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for r in reader:
                if r:  # skip empty lines
                    rows.append(r)
    except Exception as e:
        return {"valid": False, "issues": [f"CSV unreadable: {e}"], "rows": 0, "cols": 0}

    if len(rows) < min_rows:
        issues.append(f"CSV contains {len(rows)} rows; minimum required is {min_rows}.")
    
    headers = rows[0] if rows else []
    if len(headers) < min_cols:
        issues.append(f"CSV has {len(headers)} columns; minimum required is {min_cols}.")
    
    # Check for empty headers
    if any(not h.strip() for h in headers):
        issues.append("CSV contains blank column headers.")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "rows": len(rows),
        "cols": len(headers),
        "headers": headers[:10]
    }


def validate_artifact(
    file_path: str,
    expected_type: Optional[str] = None,
    required_keywords: Optional[List[str]] = None,
    min_size_bytes: int = 50
) -> Dict[str, Any]:
    """
    Unified validation pipeline for generated deliverables (PDF, DOCX, XLSX, CSV).
    Ensures deliverables are not mere dummy or empty files.
    """
    path = Path(file_path)
    checks_passed = []
    issues = []

    # 1. File exists check
    if not path.exists():
        logger.warning(f"[ARTIFACT_VALIDATOR] File does not exist: {file_path}")
        return {
            "success": False,
            "valid": False,
            "file_path": str(file_path),
            "issues": [f"File not found on disk: {file_path}"],
            "checks_passed": []
        }
    checks_passed.append("file_exists")

    # Size check
    file_size = os.path.getsize(file_path)
    if file_size < min_size_bytes:
        issues.append(f"File size too small ({file_size} bytes); likely incomplete or empty.")
    else:
        checks_passed.append("file_has_content")

    ext = path.suffix.lower().lstrip(".")
    detected_type = expected_type.lower() if expected_type else ext
    extracted_text = ""
    details = {}

    # 2. Format-specific structure and readability checks
    if detected_type in ["xlsx", "excel"]:
        try:
            from tools.validators.xlsx_validator import validate_xlsx_artifact
            res = validate_xlsx_artifact(str(path))
            if not res.get("valid"):
                issues.extend(res.get("issues", []))
            else:
                checks_passed.append("readable_structure")
            details["xlsx"] = res
        except Exception as e:
            issues.append(f"XLSX validation error: {e}")

    elif detected_type == "pdf":
        try:
            from tools.validators.pdf_validator import validate_pdf_artifact
            res = validate_pdf_artifact(str(path))
            if not res.get("valid"):
                issues.extend(res.get("issues", []))
            else:
                checks_passed.append("readable_structure")
            details["pdf"] = res
        except Exception as e:
            issues.append(f"PDF validation error: {e}")

    elif detected_type in ["docx", "word"]:
        try:
            from tools.validators.docx_validator import validate_docx_artifact
            res = validate_docx_artifact(str(path))
            if not res.get("valid"):
                issues.extend(res.get("issues", []))
            else:
                checks_passed.append("readable_structure")
            details["docx"] = res
        except Exception as e:
            issues.append(f"DOCX validation error: {e}")

    elif detected_type == "csv":
        res = validate_csv(str(path))
        if not res.get("valid"):
            issues.extend(res.get("issues", []))
        else:
            checks_passed.append("readable_structure")
        details["csv"] = res

    # 3. Content relevance and anti-placeholder check
    # Try reading text snippet to verify relevance
    try:
        sample_text = ""
        if detected_type in ["csv", "txt"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                sample_text = f.read(4000).lower()
        elif detected_type == "xlsx":
            import openpyxl
            wb = openpyxl.load_workbook(str(path), data_only=True)
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    sample_text += " " + " ".join(str(c) for c in row if c is not None)
                if len(sample_text) > 4000:
                    break
            sample_text = sample_text.lower()

        if sample_text:
            # Check for dummy placeholders
            if any(ph in sample_text for ph in DUMMY_PLACEHOLDERS):
                issues.append("Document contains placeholder or dummy text.")
            else:
                checks_passed.append("no_placeholders")

            # Check required domain keywords if supplied
            if required_keywords:
                matched_kw = [kw for kw in required_keywords if kw.lower() in sample_text]
                if not matched_kw:
                    issues.append(f"Missing expected domain keywords: {required_keywords}")
                else:
                    checks_passed.append("domain_keywords_present")
                    details["matched_keywords"] = matched_kw
    except Exception as e:
        logger.debug(f"[ARTIFACT_VALIDATOR] Text sampling notice: {e}")

    is_valid = len(issues) == 0
    score = max(0, 100 - len(issues) * 25)

    logger.info(
        f"[ARTIFACT_VALIDATOR] File: '{path.name}' | Type: {detected_type} | "
        f"Valid: {is_valid} | Score: {score} | Checks: {checks_passed} | Issues: {issues}"
    )

    return {
        "success": is_valid,
        "valid": is_valid,
        "score": score,
        "file_path": str(path),
        "file_name": path.name,
        "file_size_bytes": file_size,
        "detected_type": detected_type,
        "checks_passed": checks_passed,
        "issues": issues,
        "details": details
    }
