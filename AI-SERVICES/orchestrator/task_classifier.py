"""
Strict Structured Task Classifier for Sovereign AI Workbench.
SIH 26117 — Deterministic First-Stage Task Classifier and Specialist Router.
Hardware-Aware (NVIDIA RTX 2050 4GB GPU & CPU-Only Profiles).

Ensures deterministic mapping:
- USER REQUEST + ATTACHMENT ANALYSIS
  ↓
  TASK CLASSIFIER
  ↓
  AGENT SELECTION
  ↓
  MODEL SELECTION
  ↓
  TOOL SELECTION
"""

import re
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field

from core.logging import logger
from core.config import settings
from core.hardware import get_hardware_profile, PROFILE_GPU_RTX2050


class TaskType(str, Enum):
    GENERAL = "GENERAL"
    REASONING = "REASONING"
    CODING = "CODING"
    CODE_GENERATION = "CODE_GENERATION"
    CODE_EXECUTION = "CODE_EXECUTION"
    DOCUMENT_COUNT = "DOCUMENT_COUNT"
    DOCUMENT_LIST = "DOCUMENT_LIST"
    DOCUMENT_METADATA = "DOCUMENT_METADATA"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    DOCUMENT_QA = "DOCUMENT_QA"
    VISION = "VISION"
    IMAGE_IDENTIFICATION = "IMAGE_IDENTIFICATION"
    OCR = "OCR"
    RAG = "RAG"
    EXCEL = "EXCEL"
    EXCEL_GENERATION = "EXCEL_GENERATION"
    PDF_GENERATION = "PDF_GENERATION"
    DOCX_GENERATION = "DOCX_GENERATION"
    FILE_OPERATION = "FILE_OPERATION"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    MAINTENANCE = "MAINTENANCE"
    MAINTENANCE_ANALYSIS = "MAINTENANCE_ANALYSIS"
    SAFETY = "SAFETY"
    SAFETY_ANALYSIS = "SAFETY_ANALYSIS"
    COMPLIANCE = "COMPLIANCE"
    COMPLIANCE_ANALYSIS = "COMPLIANCE_ANALYSIS"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    REPORTING = "REPORTING"
    REPORT_GENERATION = "REPORT_GENERATION"
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    SIMPLE_GREETING = "SIMPLE_GREETING"


class TaskClassification(BaseModel):
    """Pydantic validated structured task classification result."""
    task_type: str = Field(..., description="Classified task category")
    agent: str = Field(default="general", description="Assigned specialist agent slug")
    requires_vision: bool = Field(default=False, description="Whether visual processing is needed")
    requires_rag: bool = Field(default=False, description="Whether vector search/RAG is needed")
    requires_tools: bool = Field(default=False, description="Whether tool/sandbox execution is needed")
    requires_memory: bool = Field(default=True, description="Whether memory context should be loaded")
    complexity: str = Field(default="low", description="Task complexity: low, medium, high")
    recommended_model: str = Field(default="qwen2.5:1.5b", description="Recommended model name")
    confidence: float = Field(default=0.90, ge=0.0, le=1.0, description="Classification confidence score")
    reasoning: Optional[str] = Field(default=None, description="Short classification rationale")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class TaskClassifier:
    """Intelligent deterministic task classifier with exact intent and specialist agent routing."""

    def __init__(self):
        self.supported_types = [t.value for t in TaskType]

    def _determine_recommended_model(
        self,
        task_type: str,
        complexity: str,
        requires_vision: bool,
        hardware_profile: str
    ) -> str:
        """Helper to pick model recommendation matching target hardware stack."""
        is_gpu = hardware_profile == PROFILE_GPU_RTX2050

        # Deterministic document metadata tasks - zero LLM
        if task_type in [TaskType.DOCUMENT_COUNT.value, TaskType.DOCUMENT_LIST.value, TaskType.DOCUMENT_METADATA.value]:
            return "deterministic_mongodb"

        # Vision and OCR use Vision LLM
        if requires_vision or task_type in [TaskType.VISION.value, TaskType.OCR.value, TaskType.IMAGE_IDENTIFICATION.value]:
            return getattr(settings, "GPU_VISION_MODEL", "qwen3-vl:4b") if is_gpu else getattr(settings, "CPU_VISION_MODEL", "qwen2.5vl:3b")

        # ONLY actual coding tasks use the code model
        if task_type in [TaskType.CODING.value, TaskType.CODE_GENERATION.value, TaskType.CODE_EXECUTION.value]:
            return getattr(settings, "GPU_CODER_MODEL", "qwen2.5-coder:1.5b") if is_gpu else getattr(settings, "CPU_CODER_MODEL", "qwen2.5-coder:1.5b")

        # Deep document reasoning, QA, reporting, and industrial analysis use Qwen3:4B on GPU
        if task_type in [
            TaskType.DOCUMENT_QA.value, TaskType.DOCUMENT_ANALYSIS.value,
            TaskType.REPORTING.value, TaskType.REPORT_GENERATION.value,
            TaskType.PDF_GENERATION.value, TaskType.MAINTENANCE.value,
            TaskType.MAINTENANCE_ANALYSIS.value, TaskType.SAFETY.value,
            TaskType.SAFETY_ANALYSIS.value, TaskType.COMPLIANCE.value,
            TaskType.COMPLIANCE_ANALYSIS.value, TaskType.RISK_ANALYSIS.value,
            TaskType.REASONING.value
        ]:
            return getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b") if is_gpu else getattr(settings, "CPU_MAIN_MODEL", "qwen2.5:1.5b")

        # General conversational chat uses lightweight model
        return getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b") if is_gpu else getattr(settings, "CPU_MAIN_MODEL", "qwen2.5:1.5b")

    def rule_based_classify(
        self,
        message: str,
        has_images: bool = False,
        has_files: bool = False,
        file_type: Optional[str] = None
    ) -> TaskClassification:
        """
        Deterministic, attachment-aware task classification.
        Enforces SIH 26117 Agent Responsibility Matrix:
        General -> Coding -> Spreadsheet -> Reporting -> Document -> Vision -> OCR
        """
        text = (message or "").lower().strip()
        hw_profile = get_hardware_profile()

        def contains_phrase(*phrases: str) -> bool:
            return any(phrase in text for phrase in phrases)

        def contains_regex(pattern: str) -> bool:
            return bool(re.search(pattern, text, re.IGNORECASE))

        # ─── 1. Pure Greetings (Bypass agent loops) ─────────────────────────
        _GREETING_PATTERNS = re.compile(
            r"^(hi|hello|hey|good morning|good evening|good afternoon|good night|"
            r"namaste|howdy|greetings|what\'?s up|sup|yo|hola|bonjour)[.!?,\s]*$",
            re.IGNORECASE
        )
        if _GREETING_PATTERNS.match(text) and not has_images and not has_files:
            fallback_model = getattr(settings, "GPU_FALLBACK_MODEL", "qwen2.5:0.5b") if "GPU" in hw_profile.upper() else "qwen2.5:0.5b"
            return TaskClassification(
                task_type=TaskType.SIMPLE_GREETING.value,
                agent="general",
                requires_vision=False,
                requires_rag=False,
                requires_tools=False,
                requires_memory=False,
                complexity="trivial",
                recommended_model=fallback_model,
                confidence=0.99,
                reasoning="Pure greeting detected — bypass agent loop, use ultra-fast model."
            )

        # ─── 1.5. Deterministic Document Store Queries (ZERO LLM / ZERO RAG - Section 5) ─
        is_doc_count = contains_phrase(
            "how many document", "how many documents", "count document", "count documents",
            "number of document", "number of documents", "total document", "total documents",
            "how many files do i have", "how many files are uploaded"
        )
        if is_doc_count:
            return TaskClassification(
                task_type=TaskType.DOCUMENT_COUNT.value,
                agent="document_tool",
                requires_vision=False,
                requires_rag=False,
                requires_tools=True,
                requires_memory=False,
                complexity="trivial",
                recommended_model="deterministic_mongodb",
                confidence=1.0,
                reasoning="Deterministic document count requested -> MongoDB metadata directly (Section 5)."
            )

        is_doc_list = contains_phrase(
            "list document", "list documents", "list my documents", "show documents",
            "show all documents", "what documents are uploaded", "all documents",
            "uploaded documents", "list uploaded documents"
        ) and not contains_phrase("in this document", "from this document", "inside document")
        if is_doc_list:
            return TaskClassification(
                task_type=TaskType.DOCUMENT_LIST.value,
                agent="document_tool",
                requires_vision=False,
                requires_rag=False,
                requires_tools=True,
                requires_memory=False,
                complexity="trivial",
                recommended_model="deterministic_mongodb",
                confidence=1.0,
                reasoning="Deterministic document list requested -> MongoDB list_documents directly (Section 5)."
            )

        # ─── 2. Document Extraction -> Spreadsheet Workflow (PRIORITY OVER PURE EXCEL) ─
        is_doc_to_excel = contains_phrase(
            "extract the inspection records and create an excel",
            "extract the inspection records and create an excel sheet",
            "extract inspection records and create an excel",
            "extract records and create an excel",
            "extract data and create an excel"
        )
        if is_doc_to_excel:
            rec_model = getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b")
            return TaskClassification(
                task_type=TaskType.DOCUMENT_ANALYSIS.value,
                agent="document_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="high",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Document Extraction -> Spreadsheet workflow: Document Agent extracts records -> Spreadsheet Agent creates XLSX."
            )

        # ─── 2.5. Report Generation (PRIORITY when user asks to generate/create report) ─
        is_report_gen = (
            text.startswith("generate report") or text.startswith("create report") or
            contains_phrase("generate a report", "create a report", "generate an inspection report", "create an inspection report", "generate report with", "compile report")
        ) and not any(k in text for k in ["summarize", "what is", "how many", "explain", "extract", "find"]) and not is_doc_to_excel
        if is_report_gen:
            rec_model = getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b")
            return TaskClassification(
                task_type=TaskType.REPORT_GENERATION.value,
                agent="reporting_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="medium",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Report generation requested -> Reporting Agent + ReportLab / openpyxl tool (Section 41)."
            )

        # ─── 2.6. File / Folder System Operations (Filesystem Agent) ──────────
        is_file_op = any(k in text for k in [
            "create folder", "create a folder", "folder called", "mkdir", "make directory",
            "delete file", "move file", "rename file", "list files", "save file"
        ])
        if is_file_op:
            rec_model = getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b")
            return TaskClassification(
                task_type=TaskType.FILE_OPERATION.value,
                agent="filesystem_agent",
                requires_vision=False,
                requires_rag=False,
                requires_tools=True,
                requires_memory=False,
                complexity="low",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Filesystem operation requested -> Filesystem Agent + local file tools."
            )

        # ─── 3. Spreadsheet / Excel File Generation (PRIORITY OVER GENERAL & CODER) ─
        # User asks for an Excel/Spreadsheet file artifact, NOT Python code.
        is_excel_req = contains_phrase(
            "create an excel", "create excel", "generate excel", "generate an excel",
            "make excel", "make an excel", "create xlsx", "generate xlsx", "make xlsx",
            "create spreadsheet", "generate spreadsheet", "export to excel", "export as excel",
            "save as excel", "save to excel", "excel file", "excel sheet", ".xlsx file"
        ) or (
            contains_phrase("excel", "xlsx", "spreadsheet") and any(k in text for k in ["create", "generate", "build", "make", "export", "file", "sheet", "dataset", "data"])
        )
        if is_excel_req:
            # Model is General/Reasoning LLM that plans and invokes the openpyxl spreadsheet tool (Section 17)
            rec_model = getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b")
            return TaskClassification(
                task_type=TaskType.EXCEL_GENERATION.value,
                agent="spreadsheet_agent",
                requires_vision=False,
                requires_rag=has_files or contains_phrase("document", "report", "extracted"),
                requires_tools=True,
                requires_memory=True,
                complexity="medium",
                recommended_model=rec_model,
                confidence=0.99,
                reasoning="Spreadsheet / Excel artifact generation requested -> Spreadsheet Agent + Python openpyxl tool (Section 17)."
            )

        # ─── 4. PDF Report Generation ─────────────────────────────────────────
        # User asks for a compiled PDF deliverable, NOT textual stubs.
        is_pdf_req = contains_phrase(
            "create pdf", "generate pdf", "make pdf", "compile pdf", "export to pdf",
            "export as pdf", "pdf report", "inspection report pdf", "create a pdf", "generate a pdf"
        ) or (
            contains_phrase("pdf") and any(k in text for k in ["create", "generate", "compile", "report", "findings", "export"])
        )
        if is_pdf_req:
            rec_model = getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b")
            return TaskClassification(
                task_type=TaskType.PDF_GENERATION.value,
                agent="reporting_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="medium",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="PDF report compilation requested -> Reporting Agent + ReportLab tool (Section 18)."
            )

        # ─── 4. Code Execution (Sandbox Tool) ──────────────────────────────────
        is_code_exec = contains_phrase(
            "run this code", "run this python", "execute this code", "execute python",
            "run python", "run script", "execute the code", "test this code"
        )
        if is_code_exec:
            rec_model = getattr(settings, "GPU_CODER_MODEL", "qwen2.5-coder:1.5b")
            return TaskClassification(
                task_type=TaskType.CODE_EXECUTION.value,
                agent="code_agent",
                requires_vision=False,
                requires_rag=False,
                requires_tools=True,
                requires_memory=True,
                complexity="medium",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Code execution requested -> Code Sandbox Tool."
            )

        # ─── 5. Code Generation & Debugging (Coding Agent + Coder Model) ───────
        is_code_gen = contains_phrase(
            "generate python code", "write python code", "write code", "generate code",
            "write a python", "generate a python", "python script", "write a function",
            "write a script", "debug this", "write an algorithm", "create a function",
            "javascript code", "fastapi backend", "node script", "coding task"
        ) or contains_regex(r"\b(write|generate|create|debug|refactor)\s+(python|javascript|typescript|c\+\+|java|sql|node|fastapi|backend|frontend)\s+code\b") or contains_regex(r"\b(write|generate)\s+code\s+for\b")
        if is_code_gen:
            rec_model = getattr(settings, "GPU_CODER_MODEL", "qwen2.5-coder:1.5b")
            return TaskClassification(
                task_type=TaskType.CODE_GENERATION.value,
                agent="code_agent",
                requires_vision=False,
                requires_rag=False,
                requires_tools=True,
                requires_memory=True,
                complexity="high",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Code generation / debugging requested -> Coding Agent + qwen2.5-coder:1.5b."
            )

        # ─── 6. OCR Text Extraction (RapidOCR Pipeline) ───────────────────────
        is_ocr = contains_phrase(
            "ocr", "extract text from image", "extract all visible text", "extract all text",
            "read text from image", "transcribe image", "scanned document text", "extract serial number from this image"
        )
        if is_ocr:
            rec_model = getattr(settings, "GPU_VISION_MODEL", "qwen3-vl:4b")
            return TaskClassification(
                task_type=TaskType.OCR.value,
                agent="ocr_agent",
                requires_vision=True,
                requires_rag=False,
                requires_tools=True,
                requires_memory=True,
                complexity="medium",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="OCR text extraction requested -> RapidOCR Engine."
            )

        # ─── 7. Image Understanding / Visual Inspection (Vision Agent + Vision LLM) ──
        # Distinguish conceptual questions like "Explain what a P&ID is" from actual image inspection!
        is_conceptual_pid = contains_phrase("explain what a p&id", "what is a p&id", "define p&id", "what is p&id", "explain p&id")
        is_visual_inspection = (has_images and not is_ocr) or (
            not is_conceptual_pid and any(k in text for k in [
                "what component is shown", "identify this component", "identify this industrial component",
                "identify component", "identify industrial component", "identify from image",
                "in this image", "attached image", "this photo", "inspect this picture",
                "visual inspection", "damage on the surface", "cracks in the casing"
            ])
        )
        if is_visual_inspection:
            rec_model = getattr(settings, "GPU_VISION_MODEL", "qwen3-vl:4b")
            return TaskClassification(
                task_type=TaskType.VISION.value,
                agent="vision_agent",
                requires_vision=True,
                requires_rag=False,
                requires_tools=True,
                requires_memory=True,
                complexity="medium",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Visual scene understanding / component identification -> Vision Agent + qwen3-vl:4b."
            )

        # ─── 8. Document -> Excel / Table Extraction Workflow ─────────────────
        is_doc_to_excel = contains_phrase(
            "extract the inspection records and create an excel",
            "extract the inspection records and create an excel sheet",
            "extract inspection records and create an excel"
        )
        if is_doc_to_excel:
            rec_model = getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b")
            return TaskClassification(
                task_type=TaskType.DOCUMENT_ANALYSIS.value,
                agent="document_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="high",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Document Extraction -> Spreadsheet workflow: Document Agent extracts records -> Spreadsheet Agent creates XLSX."
            )

        # ─── 9. Table Extraction ──────────────────────────────────────────────
        is_table_extraction = contains_phrase(
            "extract this table", "extract table", "extract the table", "table into structured data",
            "parse table"
        )
        if is_table_extraction:
            rec_model = getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b")
            agent = "spreadsheet_agent" if contains_phrase("excel", "sheet", "csv") else "document_agent"
            return TaskClassification(
                task_type=TaskType.DOCUMENT_ANALYSIS.value,
                agent=agent,
                requires_vision=has_images,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="medium",
                recommended_model=rec_model,
                confidence=0.97,
                reasoning="Table extraction requested -> Document/Spreadsheet Agent."
            )

        # ─── 9. Industrial Maintenance Analysis (Maintenance Agent + Qwen3:4b) ─
        is_maintenance = contains_phrase(
            "maintenance analysis", "maintenance risk", "maintenance report", "maintenance inspection",
            "vibration analysis", "bearing wear", "bearing failure", "equipment failure", "mttr",
            "breakdown", "pump maintenance", "turbine maintenance", "maintenance tracker"
        ) or (contains_phrase("maintenance", "vibration", "bearing") and any(k in text for k in ["analyze", "analysis", "report", "failure", "risk", "check", "inspect"]))
        if is_maintenance:
            rec_model = getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b")
            return TaskClassification(
                task_type=TaskType.MAINTENANCE_ANALYSIS.value,
                agent="maintenance_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="high",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Industrial maintenance analysis requested -> Maintenance Agent + Qwen3:4b (Section 15)."
            )

        # ─── 10. Plant Safety & LOTO Analysis (Safety Agent + Qwen3:4b) ─────────
        is_safety = contains_phrase(
            "safety analysis", "safety report", "safety inspection", "hazard identification",
            "lockout tagout", "loto", "ppe compliance", "worker safety", "safety protocol",
            "incident report", "safety violation", "unsafe condition", "safety hazard", "safety hazards"
        ) or (contains_phrase("safety", "hazard", "hazards", "ppe", "loto", "lockout") and any(k in text for k in ["identify", "check", "analyze", "analysis", "report", "protocol", "violation", "scenario", "risk", "prevention"]))
        if is_safety:
            rec_model = getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b")
            return TaskClassification(
                task_type=TaskType.SAFETY_ANALYSIS.value,
                agent="safety_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="high",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Industrial safety analysis requested -> Safety Agent + Qwen3:4b (Section 15)."
            )

        # ─── 11. Compliance & Audit Analysis (Compliance Agent + Qwen3:4b) ──────
        is_compliance = contains_phrase(
            "compliance analysis", "compliance report", "regulatory compliance", "audit finding",
            "iso compliance", "osha compliance", "against sop", "standards compliance",
            "non-compliance", "regulatory audit", "statutory compliance"
        ) or (contains_phrase("compliance", "audit", "standard") and any(k in text for k in ["analyze", "analysis", "report", "violation", "check"]))
        if is_compliance:
            rec_model = getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b")
            return TaskClassification(
                task_type=TaskType.COMPLIANCE_ANALYSIS.value,
                agent="compliance_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="high",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Compliance / audit analysis requested -> Compliance Agent + Qwen3:4b (Section 15)."
            )

        # ─── 12. Risk Analysis & FMEA (Risk Agent + Qwen3:4b) ───────────────────
        is_risk = contains_phrase(
            "risk analysis", "risk assessment", "hazard analysis", "fmea", "risk priority number",
            "rpn", "failure mode", "severity rating", "risk mitigation", "risk evaluation"
        ) or (contains_phrase("risk", "fmea") and any(k in text for k in ["analyze", "analysis", "report", "assess", "assessment", "matrix", "mitigation"]))
        if is_risk:
            rec_model = getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b")
            return TaskClassification(
                task_type=TaskType.RISK_ANALYSIS.value,
                agent="risk_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="high",
                recommended_model=rec_model,
                confidence=0.98,
                reasoning="Risk analysis / FMEA requested -> Risk Agent + Qwen3:4b (Section 15)."
            )

        # ─── 13. Document QA / Specific Document Inquiries (Document Agent + RAG + Qwen3:4b) ─
        is_doc_qa = has_files or contains_phrase(
            "uploaded", "inspection report", "in unit 4", "in unit 3", "unit 4", "unit 3",
            "recorded pressure", "pressure recorded", "temperature recorded", "inspection date",
            "what was the pressure", "what is the pressure", "what was the temperature",
            "what does the document say", "what is in the document", "summarize document",
            "according to document", "operating pressure of", "operating temperature",
            "sop manual", "turbine operating manual"
        ) or contains_regex(r"\b(what|where|when|which|who|how much)\b.*\b(document|report|manual|sop|unit|turbine|pressure|temperature|vibration|bearing|sensor)\b")
        if is_doc_qa:
            rec_model = getattr(settings, "GPU_REASONING_MODEL", "qwen3:4b")
            return TaskClassification(
                task_type=TaskType.DOCUMENT_QA.value,
                agent="document_agent",
                requires_vision=False,
                requires_rag=True,
                requires_tools=True,
                requires_memory=True,
                complexity="medium",
                recommended_model=rec_model,
                confidence=0.97,
                reasoning="Document question / technical retrieval requested -> Document Intelligence Agent + Qdrant RAG + Qwen3:4b (Section 9)."
            )

        # ─── 10. Conceptual Definitional Questions (General Assistant) ─────────
        # e.g. "Explain what a P&ID is.", "What is preventive maintenance?"
        is_definitional = any(text.startswith(prefix) for prefix in [
            "what is ", "what are ", "define ", "tell me about ", "explain what is ",
            "explain what a ", "explain ", "who are you", "what can you do"
        ])
        if is_definitional and not has_files and not has_images:
            rec_model = getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b")
            return TaskClassification(
                task_type=TaskType.GENERAL.value,
                agent="general",
                requires_vision=False,
                requires_rag=False,
                requires_tools=False,
                requires_memory=True,
                complexity="low",
                recommended_model=rec_model,
                confidence=0.96,
                reasoning="General conceptual definition or explanation -> General Assistant."
            )

        # ─── 11. General Default Fallback ─────────────────────────────────────
        rec_model = getattr(settings, "GPU_MAIN_MODEL", "qwen2.5:1.5b")
        return TaskClassification(
            task_type=TaskType.GENERAL.value,
            agent="general",
            requires_vision=has_images,
            requires_rag=has_files,
            requires_tools=False,
            requires_memory=True,
            complexity="low",
            recommended_model=rec_model,
            confidence=0.85,
            reasoning="Default general conversational reasoning."
        )

    def classify(
        self,
        message: str,
        has_images: bool = False,
        has_files: bool = False,
        file_type: Optional[str] = None
    ) -> TaskClassification:
        """
        Public classification method with fast deterministic first stage.
        """
        classification = self.rule_based_classify(
            message=message,
            has_images=has_images,
            has_files=has_files,
            file_type=file_type
        )
        logger.info(
            f"[TASK_CLASSIFIER] task_type={classification.task_type} "
            f"agent={classification.agent} model={classification.recommended_model} "
            f"tools={classification.requires_tools} rag={classification.requires_rag}"
        )
        return classification


# Global singleton instance
task_classifier = TaskClassifier()


def system_prompt_for(agent_slug: str) -> str:
    """Return tailored system prompt for the assigned agent slug."""
    slug = (agent_slug or "general").lower()
    if slug in ["spreadsheet_agent", "spreadsheet"]:
        return (
            "You are the Sovereign Spreadsheet and Data Analysis Agent. "
            "Your objective is to generate real, verified Microsoft Excel (.xlsx) and CSV files using available tools. "
            "When the user requests an Excel file, use `create_excel` with appropriate sheet headers and populated rows. "
            "Never return raw Python code in chat when an artifact file deliverable is requested."
        )
    if slug in ["reporting_agent", "reporting"]:
        return (
            "You are the Sovereign Reporting Agent. "
            "Your objective is to compile publication-grade PDF inspection reports and technical documentation using `create_pdf`. "
            "Synthesize comprehensive sections, tables, and findings grounded in document evidence."
        )
    if slug in ["code_agent", "coding", "coder"]:
        return (
            "You are the Sovereign Autonomous Coding Specialist. "
            "Generate production-grade, bug-free Python and backend/frontend code inside markdown code blocks. "
            "If code execution is requested, use `execute_python`."
        )
    if slug in ["document_agent", "document"]:
        return (
            "You are the Sovereign Document Intelligence Agent. "
            "You have full access to workspace documents, uploaded technical manuals, and Qdrant vector retrieval. "
            "Answer questions directly from the retrieved context with exact source citations and page numbers. "
            "Do not ask the user for information that exists in the retrieved documents."
        )
    if slug in ["vision_agent", "vision"]:
        return (
            "You are the Sovereign Industrial Vision Agent. "
            "Analyze equipment images, visual defects, gauges, and diagrams with high precision. "
            "Provide evidence-based visual descriptions."
        )
    if slug in ["ocr_agent", "ocr"]:
        return (
            "You are the Sovereign Industrial OCR Agent. "
            "Extract exact alphanumeric text, equipment serial tags, pressure readings, and table data."
        )
    return (
        "You are the Sovereign On-Premise AI Agent Workbench assistant. "
        "You provide helpful, grounded, and concise engineering assistance."
    )


# Centralized dictionary of default agent system prompts
AGENT_PROMPTS: Dict[str, str] = {
    slug: system_prompt_for(slug)
    for slug in [
        "general", "code_agent", "spreadsheet_agent", "reporting_agent",
        "document_agent", "vision_agent", "ocr_agent", "risk_agent",
        "compliance_agent", "safety_agent", "maintenance_agent"
    ]
}
