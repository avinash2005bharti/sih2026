from pathlib import Path
from typing import Any, Dict, List, Optional
import pypdf
from core.logging import logger

FORBIDDEN_PLACEHOLDERS = [
    "[insert", "todo", "lorem ipsum", "placeholder", "tbd", "<replace", "[your name", "sample text", "dummy text"
]

def validate_pdf_artifact(
    file_path: str,
    required_sections: Optional[List[str]] = None,
    min_pages: int = 1,
    min_chars: int = 150
) -> Dict[str, Any]:
    """
    Mandatory PDF Artifact Validator:
    Inspects generated PDF to guarantee genuine utility, readable content,
    page completeness, absence of placeholders, and required sections.
    """
    path = Path(file_path)
    issues: List[str] = []
    missing_reqs: List[str] = []
    corrections: List[str] = []

    # 1. Existence check
    if not path.exists():
        return {
            "valid": False,
            "score": 0,
            "issues": [f"File does not exist: {file_path}"],
            "missing_requirements": ["PDF file generation"],
            "corrections": ["Generate the PDF file to the specified path."]
        }

    # 2. File size check
    if path.stat().st_size < 500:
        issues.append(f"PDF file size is suspiciously small ({path.stat().st_size} bytes).")

    # 3. Readability & Page Count
    try:
        reader = pypdf.PdfReader(str(path))
        num_pages = len(reader.pages)
        if num_pages < min_pages:
            issues.append(f"PDF has only {num_pages} pages; expected at least {min_pages}.")
            missing_reqs.append("Minimum page count")
    except Exception as e:
        return {
            "valid": False,
            "score": 0,
            "issues": [f"PDF cannot be opened or parsed: {str(e)}"],
            "missing_requirements": ["Valid readable PDF"],
            "corrections": ["Regenerate PDF using ReportLab with valid canvas stream."]
        }

    # 4. Extract Text & Check Blank Pages
    all_text = ""
    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        cleaned = page_text.strip()
        if len(cleaned) < 30:
            issues.append(f"Page {idx + 1} appears blank or contains almost no readable text.")
            missing_reqs.append(f"Content on page {idx + 1}")
        all_text += "\n" + page_text

    if len(all_text.strip()) < min_chars:
        issues.append(f"Total extracted text ({len(all_text.strip())} chars) is below threshold ({min_chars} chars).")
        missing_reqs.append("Comprehensive report content")

    # 5. Check Required Sections
    sections = required_sections or [
        "Executive Summary",
        "Equipment",
        "Inspection",
        "Risk",
        "Recommendation"
    ]
    lower_text = all_text.lower()
    for sec in sections:
        if sec.lower() not in lower_text:
            issues.append(f"Required section '{sec}' was not found in PDF.")
            missing_reqs.append(f"Section: {sec}")
            corrections.append(f"Add a dedicated section titled '{sec}' with supporting data.")

    # 6. Check Placeholder Text
    for placeholder in FORBIDDEN_PLACEHOLDERS:
        if placeholder in lower_text:
            issues.append(f"PDF contains placeholder text: '{placeholder}'")
            corrections.append(f"Replace placeholder '{placeholder}' with authentic factual information.")

    # Compute quality score
    score = 100
    score -= len(issues) * 20
    score = max(0, min(100, score))

    is_valid = len(issues) == 0

    logger.info(
        f"PDF VALIDATION | File: {path.name} | Valid: {is_valid} | Score: {score} | "
        f"Issues: {len(issues)} | Missing: {len(missing_reqs)}"
    )

    return {
        "valid": is_valid,
        "score": score,
        "issues": issues,
        "missing_requirements": missing_reqs,
        "corrections": corrections,
        "metadata": {
            "page_count": num_pages,
            "total_chars": len(all_text.strip()),
            "file_size_bytes": path.stat().st_size
        }
    }
