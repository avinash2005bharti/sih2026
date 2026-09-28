from pathlib import Path
from typing import Any, Dict, List, Optional
import docx
from core.logging import logger

def validate_docx_artifact(
    file_path: str,
    required_headings: Optional[List[str]] = None,
    min_paragraphs: int = 3
) -> Dict[str, Any]:
    """
    Mandatory Word (.docx) Artifact Validator:
    Inspects document existence, paragraph volume, heading hierarchy,
    and required industrial content sections.
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
            "missing_requirements": ["Word document generation"],
            "corrections": ["Generate the DOCX file using python-docx."]
        }

    try:
        doc = docx.Document(str(path))
    except Exception as e:
        return {
            "valid": False,
            "score": 0,
            "issues": [f"Failed to open DOCX: {str(e)}"],
            "missing_requirements": ["Valid DOCX format"],
            "corrections": ["Re-save document with standard python-docx structures."]
        }

    non_empty_paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    if len(non_empty_paras) < min_paragraphs:
        issues.append(f"Document has only {len(non_empty_paras)} paragraphs; expected at least {min_paragraphs}.")
        missing_reqs.append("Comprehensive narrative content")

    all_text = "\n".join(non_empty_paras).lower()

    if required_headings:
        for heading in required_headings:
            if heading.lower() not in all_text:
                issues.append(f"Required section or heading '{heading}' was not found.")
                missing_reqs.append(f"Heading: {heading}")
                corrections.append(f"Add a heading '{heading}' with relevant documentation.")

    score = 100 - (len(issues) * 20)
    score = max(0, min(100, score))
    is_valid = len(issues) == 0

    logger.info(
        f"DOCX VALIDATION | File: {path.name} | Valid: {is_valid} | Score: {score} | "
        f"Paragraphs: {len(non_empty_paras)} | Tables: {len(doc.tables)}"
    )

    return {
        "valid": is_valid,
        "score": score,
        "issues": issues,
        "missing_requirements": missing_reqs,
        "corrections": corrections,
        "metadata": {
            "paragraph_count": len(non_empty_paras),
            "table_count": len(doc.tables)
        }
    }
