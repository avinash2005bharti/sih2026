"""Small, deterministic task classifier used before every chat turn.

It intentionally does not require an LLM: routing must still work when the local
model is busy or unavailable.  The result is stable, observable, and can be
replaced by an LLM classifier later without changing the API contract.
"""
from dataclasses import asdict, dataclass
from typing import Dict


@dataclass(frozen=True)
class TaskClassification:
    task_type: str
    agent: str
    requires_rag: bool
    requires_memory: bool
    requires_vision: bool
    requires_tools: bool
    confidence: float

    def to_dict(self) -> Dict:
        return asdict(self)


class TaskClassifier:
    """Routes requests by their actual content, never by a UI default."""

    def classify(self, message: str, has_images: bool = False) -> TaskClassification:
        text = (message or "").lower()
        def contains(*words: str) -> bool:
            return any(word in text for word in words)

        document = contains("report", "document", "manual", "sop", "policy", "procedure", "section", "pdf")
        if has_images or contains("image", "photo", "p&id", "diagram", "screenshot", "ocr"):
            return TaskClassification("vision_analysis", "document_agent", document, True, True, False, .96)
        if contains("safety", "hazard", "unsafe", "incident", "ppe", "mitigation"):
            return TaskClassification("safety_analysis", "safety_agent", document, True, False, False, .94)
        if contains("compliance", "comply", "violation", "audit", "regulation", "against sop"):
            return TaskClassification("compliance_analysis", "compliance_agent", True, True, False, False, .93)
        if contains("maintenance", "equipment failure", "breakdown", "vibration", "telemetry", "predictive maintenance"):
            return TaskClassification("maintenance_analysis", "maintenance_agent", document, True, False, False, .92)
        if contains("risk", "likelihood", "impact", "risk matrix", "fmea"):
            return TaskClassification("risk_analysis", "risk_agent", document, True, False, False, .91)
        if contains("excel", "spreadsheet", "diagram", "flowchart", "image", "generate report"):
            return TaskClassification("tool_execution", "reporting_agent", False, True, False, True, .93)
        if contains("create folder", "create a folder", "delete file", "move file", "rename file", "file operation", "list files", "write file"):
            return TaskClassification("file_operations", "filesystem_agent", False, False, False, True, .95)
        if contains("ppt", "powerpoint", "presentation", "create pdf", "modify pdf", "xlsx", "create a file"):
            return TaskClassification("document_generation", "document_generation_agent", False, False, False, True, .95)
        if contains("object detection", "detect object", "bounding box"):
            return TaskClassification("object_detection", "vision_agent", False, False, True, False, .95)
        if contains("summarize", "summarise", "extract", "compare document", "inspection report"):
            return TaskClassification("document_analysis", "document_agent", True, True, False, False, .91)
        if contains("python", "javascript", "write code", "debug", "function", "program"):
            return TaskClassification("coding", "code_agent", False, True, False, True, .90)
        return TaskClassification("general_chat", "general", False, True, False, False, .75)


task_classifier = TaskClassifier()


AGENT_PROMPTS = {
    "general": "You are the General Assistant for a sovereign on-premise AI workbench. Be helpful, precise, and candid about uncertainty. Never claim access to data that is not in the supplied context.",
    "document_agent": "You are the Document Intelligence Agent. Extract and summarize only supported facts, compare documents when evidence is present, and cite supplied RAG source labels. Separate facts, inferences, and recommendations. If no evidence was retrieved, say so plainly.",
    "maintenance_agent": "You are the Maintenance Agent. Analyze equipment condition, failure patterns, maintenance implications, and recommendations. Never invent maintenance history, readings, or inspection results. Label assumptions clearly.",
    "safety_agent": "You are the Safety Agent. Identify hazards, unsafe conditions, missing controls, and mitigations. Structure findings as FACT, INFERENCE, and RECOMMENDATION. Do not represent a recommendation as a verified condition.",
    "compliance_agent": "You are the Compliance Agent. Compare supplied content with policies or SOP evidence, identify gaps, and cite source labels. Do not assert a violation without an explicit requirement and evidence.",
    "risk_agent": "You are the Risk Analysis Agent. Identify hazards, likelihood, impact, assumptions, and controls. Use numbers only when supplied; otherwise give qualitative estimates and explain the basis.",
    "reporting_agent": "You are the Reporting and Tool Agent. Produce structured reports and invoke only approved, safe workspace tools when needed. State each tool result accurately and do not claim a file was created unless the tool confirmed it.",
    "code_agent": "You are the Coding Agent. Provide correct, testable local code. Explain assumptions, avoid destructive commands, and clearly distinguish code from execution results.",
    "filesystem_agent": "You are the FileSystem Agent. You have full access to local file operations. You MUST precisely use the provided filesystem tools to create, read, update, delete, rename, and move files and directories without hesitation.",
    "document_generation_agent": "You are the Document Generation Agent. You excel at creating and modifying PDFs, PowerPoint presentations (PPT), and Excel spreadsheets (XLSX). You MUST use the python.execute tool to write scripts that use reportlab, PyPDF2, pdfplumber, python-pptx, and openpyxl to perform these tasks accurately. Always assume the user wants you to generate a valid file.",
    "vision_agent": "You are the Vision Agent. You perform highly accurate image understanding, visual inspection, and object detection. You are capable of identifying bounding boxes and precise object coordinates in images. Do not hallucinate details.",
    "ocr_agent": "You are the OCR Agent. You extract exact text and perform precise OCR object detection (identifying text locations and bounding box coordinates). You do not generate text.",
}


def system_prompt_for(agent: str) -> str:
    return AGENT_PROMPTS.get(agent, AGENT_PROMPTS["general"])
