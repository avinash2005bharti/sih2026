"""
Master End-to-End Architecture Benchmark Suite
SIH 26117 — Sovereign On-Premise Agentic AI Workbench
Validates all 15 Core Acceptance Criteria from Section 47 & 53.
"""

import os
import sys
import uuid
import pytest
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator.task_classifier import task_classifier, TaskType
from llm.model_router import model_router
from llm.model_registry import model_registry
from rag.document_store import document_store
from rag.chunker import document_chunker
from rag.qdrant_client import qdrant_service
from ocr.ocr_service import ocr_service
from vision.vision_service import vision_service
from tools.validators.xlsx_validator import validate_xlsx_artifact
from tools.validators.pdf_validator import validate_pdf_artifact
from tools.agent_tools import create_excel, create_pdf


# ==============================================================================
# 1. GENERAL CHAT (Section 13, 47 - Test 1)
# User: "Hello, explain what RAG is."
# Expected: GeneralAgent, qwen2.5:1.5b, NO 4B model, NO tools
# ==============================================================================
def test_01_general_chat():
    query = "Hello, explain what RAG is."
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.GENERAL.value
    assert classification.agent in ["general", "general_agent"]
    assert classification.requires_tools is False
    assert classification.requires_rag is False
    
    route = model_router.select(task_type=classification.task_type)
    assert route["selected_model"] == "qwen2.5:1.5b"
    assert route["fallback_model"] == "qwen3:1.7b"


# ==============================================================================
# 2. CODE GENERATION (Section 16, 47 - Test 2)
# User: "Write Python code to calculate factorial."
# Expected: CodingAgent, qwen2.5-coder:1.5b
# ==============================================================================
def test_02_code_generation():
    query = "Write Python code to calculate factorial."
    classification = task_classifier.classify(query)
    
    assert classification.task_type in [TaskType.CODE_GENERATION.value, "coding"]
    assert classification.agent in ["code_agent", "coding"]
    
    route = model_router.select(task_type="CODING")
    assert route["selected_model"] == "qwen2.5-coder:1.5b"
    assert route["fallback_model"] == "qwen2.5-coder:3b"


# ==============================================================================
# 3. EXCEL GENERATION (Section 17, 47 - Test 3)
# User: "Create an Excel file from this dataset."
# Expected: SpreadsheetAgent, openpyxl, verified XLSX artifact
# NOT coder model!
# ==============================================================================
def test_03_excel_generation():
    query = "Create an Excel file from this dataset."
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.EXCEL_GENERATION.value
    assert classification.agent == "spreadsheet_agent"
    assert classification.requires_tools is True
    
    # Model for Spreadsheet Agent planning is general/reasoning, NOT coder model
    route = model_router.select(task_type="EXCEL_GENERATION")
    assert "coder" not in route["selected_model"].lower()
    
    # Deterministic openpyxl execution & verification
    file_name = f"benchmark_data_{uuid.uuid4().hex[:6]}.xlsx"
    headers = ["Equipment ID", "Operating Pressure (bar)", "Temperature (C)", "Status"]
    rows = [
        ["P-101", 12.5, 85, "Normal"],
        ["P-102", 14.5, 92, "Warning"],
        ["V-204", 4.2, 45, "Normal"],
    ]
    import json
    res_str = create_excel.func(
        file_name=file_name,
        headers=headers,
        rows=rows,
        title="Industrial Equipment Metrics"
    )
    res = json.loads(res_str)
    assert res["success"] is True
    excel_path = res["file_path"]
    assert os.path.exists(excel_path)
    
    # Artifact validation
    val = validate_xlsx_artifact(excel_path)
    assert val["valid"] is True
    assert val["metadata"]["row_count"] >= 3
    assert val["metadata"]["col_count"] >= 4


# ==============================================================================
# 4. DOCUMENT COUNT — DETERMINISTIC (Section 5, 47 - Test 4)
# User: "How many documents do I have?"
# Flow: DOCUMENT_COUNT -> MongoDB / Document Registry -> count_documents()
# NO Qdrant search, NO 4B model, NO ReAct loop
# ==============================================================================
def test_04_document_count_deterministic():
    query = "How many documents do I have?"
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.DOCUMENT_COUNT.value
    assert classification.agent == "document_tool"
    assert classification.recommended_model == "deterministic_mongodb"
    assert classification.requires_rag is False
    
    # Direct deterministic execution without LLM
    doc_count = document_store.count_documents(user_id="benchmark_engineer", is_admin=True)
    assert isinstance(doc_count, int)
    assert doc_count >= 0


# ==============================================================================
# 5. DOCUMENT LIST — DETERMINISTIC (Section 5, 33)
# User: "List uploaded documents"
# Flow: DOCUMENT_LIST -> MongoDB -> list_documents()
# ==============================================================================
def test_05_document_list_deterministic():
    query = "List uploaded documents"
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.DOCUMENT_LIST.value
    assert classification.agent == "document_tool"
    assert classification.recommended_model == "deterministic_mongodb"
    assert classification.requires_rag is False
    
    docs = document_store.list_documents(user_id="benchmark_engineer", is_admin=True)
    assert isinstance(docs, list)


# ==============================================================================
# 6. DOCUMENT UPLOAD & INGESTION PIPELINE (Section 7, 10)
# Chunking -> Embedding -> Qdrant Verified Upsert -> Status Verification
# ==============================================================================
@pytest.mark.asyncio
async def test_06_document_ingestion_pipeline():
    doc_id = f"doc_benchmark_{uuid.uuid4().hex[:6]}"
    doc_name = "Centrifugal_Pump_P102_Manual.pdf"
    content = (
        "# Centrifugal Pump P-102 Operating Manual\n\n"
        "## Technical Specifications\n"
        "The standard operating pressure of P-102 is 14.5 bar under continuous duty. "
        "The scheduled inspection date is October 15, 2026. "
        "Vibration velocity limit is 3.5 mm/s. Maximum temperature threshold is 95 deg C.\n\n"
        "## Maintenance Procedure\n"
        "Mechanical seals must be flushed using synthetic ISO VG 46 lubricant."
    )
    
    # 1. Chunking
    chunks = document_chunker.chunk_document(
        text=content,
        document_id=doc_id,
        document_name=doc_name
    )
    assert len(chunks) >= 1
    assert any("14.5 bar" in c.text for c in chunks)
    
    # 2. Verified Upsert into Qdrant
    collection = "benchmark_sovereign_knowledge"
    res = await qdrant_service.upsert_chunks_verified(
        chunks=chunks,
        collection_name=collection
    )
    assert res["success"] is True
    assert res["verified"] is True
    assert res["inserted_count"] == len(chunks)


# ==============================================================================
# 7. DOCUMENT RAG QA & RETRIEVAL VERIFICATION (Section 9, 10, 47 - Test 5)
# User: "What was the operating pressure of P-102?"
# Flow: Intent=DOCUMENT_QA -> DocumentAgent -> nomic-embed-text -> Qdrant -> qwen3:4b
# ==============================================================================
@pytest.mark.asyncio
async def test_07_document_rag_retrieval_verification():
    query = "What was the operating pressure of P-102?"
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.DOCUMENT_QA.value
    assert classification.agent == "document_agent"
    assert classification.requires_rag is True
    
    # Routing verified
    route = model_router.select(task_type="DOCUMENT_QA")
    assert route["selected_model"] == "qwen3:4b"
    assert route["fallback_model"] == "qwen3:1.7b"
    
    # Retrieval verification from Qdrant
    hits = await qdrant_service.search(
        query=query,
        collection_name="benchmark_sovereign_knowledge",
        limit=3
    )
    assert len(hits) > 0, "RAG retrieval verification failed: 0 chunks returned!"
    top_hit = hits[0]
    assert top_hit["score"] > 0.0
    assert "14.5 bar" in top_hit["text"]
    assert top_hit.get("metadata", {}).get("document_name") == "Centrifugal_Pump_P102_Manual.pdf" or "14.5 bar" in top_hit["text"]


# ==============================================================================
# 8. IMAGE OCR PIPELINE (Section 21, 47 - Test 6)
# User: "Extract all visible text from this image."
# Expected: RapidOCR Engine, extract text
# ==============================================================================
def test_08_image_ocr():
    query = "Extract all visible text from this image."
    classification = task_classifier.classify(query, has_images=True)
    
    assert classification.task_type == TaskType.OCR.value
    assert classification.agent == "ocr_agent"
    assert classification.requires_vision is True
    
    # Verify OCR on real equipment image
    test_img = Path(__file__).resolve().parent.parent / "workspace" / "test_equipment_label.png"
    if not test_img.exists():
        pytest.skip("Workspace test image not present")
        
    res = ocr_service.extract_text(str(test_img))
    assert res["success"] is True
    assert "P-101" in res["text"]
    assert "12.5" in res["text"] or "bar" in res["text"]


# ==============================================================================
# 9. IMAGE UNDERSTANDING / VISION AGENT (Section 19, 47 - Test 7)
# User: "Identify this component in the image."
# Expected: VisionAgent, qwen3-vl:4b (fallback qwen2.5vl:3b)
# ==============================================================================
def test_09_image_understanding_routing():
    query = "Identify this component in the image."
    classification = task_classifier.classify(query, has_images=True)
    
    assert classification.task_type == TaskType.VISION.value
    assert classification.agent == "vision_agent"
    assert classification.requires_vision is True
    
    route = model_router.select(task_type="VISION", requires_vision=True)
    assert route["selected_model"] in ["qwen3-vl:4b", "qwen2.5vl:3b"]
    assert route["fallback_model"] == "qwen2.5vl:3b"


# ==============================================================================
# 10. PDF REPORT GENERATION (Section 18, 41)
# User: "Generate inspection report pdf"
# Flow: REPORT_GENERATION -> ReportingAgent -> reportlab -> validated PDF
# ==============================================================================
def test_10_pdf_generation():
    query = "Create a PDF inspection report from this data."
    classification = task_classifier.classify(query)
    
    assert classification.task_type in [TaskType.PDF_GENERATION.value, TaskType.REPORT_GENERATION.value]
    assert classification.agent == "reporting_agent"
    
    file_name = f"benchmark_report_{uuid.uuid4().hex[:6]}.pdf"
    import json
    res_str = create_pdf.func(
        file_name=file_name,
        title="Centrifugal Pump P-102 Inspection Report",
        content=(
            "Executive Summary: Routine tri-monthly maintenance inspection of P-102.\n"
            "Equipment Details: Centrifugal Pump P-102 operating under continuous industrial duty.\n"
            "Inspection Findings: Operating pressure stable at 14.5 bar. Temperature within limits at 85 C.\n"
            "Risk Assessment: Low operational risk identified for current operating cycle.\n"
            "Recommendation: Continue routine monitoring and schedule next quarterly check."
        ),
        columns=["Component", "Status", "Reading"],
        rows=[["Pump P-102", "Normal", "14.5 bar"], ["Valve V-204", "Normal", "4.2 bar"]]
    )
    res = json.loads(res_str)
    assert res["success"] is True
    pdf_path = res["file_path"]
    assert os.path.exists(pdf_path)
    
    # Artifact validation
    val = validate_pdf_artifact(pdf_path)
    assert val["valid"] is True
    assert val["metadata"]["page_count"] >= 1
    assert val["metadata"]["file_size_bytes"] > 500


# ==============================================================================
# 11. DOCUMENT -> EXCEL WORKFLOW (Section 47 - Test 8)
# User: "Extract the inspection records and create an Excel file."
# Flow: DocumentAgent -> extraction -> SpreadsheetAgent -> openpyxl -> XLSX
# ==============================================================================
def test_11_document_to_excel_workflow():
    query = "Extract the inspection records and create an Excel file."
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.DOCUMENT_ANALYSIS.value
    assert classification.agent == "document_agent"
    assert classification.requires_tools is True
    
    # Extracted data structure prepared by DocumentAgent
    extracted_records = [
        {"equipment": "Pump P-102", "reading": "14.5 bar", "inspection_date": "2026-10-15", "status": "Pass"},
        {"equipment": "Valve V-204", "reading": "4.2 bar", "inspection_date": "2026-10-14", "status": "Pass"}
    ]
    
    file_name = f"extracted_records_{uuid.uuid4().hex[:6]}.xlsx"
    headers = list(extracted_records[0].keys())
    rows = [[r[h] for h in headers] for r in extracted_records]
    
    import json
    res_str = create_excel.func(
        file_name=file_name,
        headers=headers,
        rows=rows,
        title="Extracted Inspection Records"
    )
    res = json.loads(res_str)
    assert res["success"] is True
    excel_path = res["file_path"]
    val = validate_xlsx_artifact(excel_path)
    assert val["valid"] is True
    assert val["metadata"]["row_count"] >= 2


# ==============================================================================
# 12. MAINTENANCE ANALYSIS (Section 15, 33)
# User: "Analyze maintenance risk and bearing vibration for Pump P-102."
# Expected: MaintenanceAgent, qwen3:4b
# ==============================================================================
def test_12_maintenance_analysis():
    query = "Analyze maintenance risk and bearing vibration for Pump P-102."
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.MAINTENANCE_ANALYSIS.value
    assert classification.agent == "maintenance_agent"
    assert classification.recommended_model == "qwen3:4b"
    
    route = model_router.select(task_type="MAINTENANCE_ANALYSIS")
    assert route["selected_model"] == "qwen3:4b"


# ==============================================================================
# 13. SAFETY ANALYSIS (Section 15, 33)
# User: "Identify safety hazards and LOTO protocols for high-pressure line."
# Expected: SafetyAgent, qwen3:4b
# ==============================================================================
def test_13_safety_analysis():
    query = "Identify safety hazards and LOTO protocols in this scenario."
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.SAFETY_ANALYSIS.value
    assert classification.agent == "safety_agent"
    assert classification.recommended_model == "qwen3:4b"
    
    route = model_router.select(task_type="SAFETY_ANALYSIS")
    assert route["selected_model"] == "qwen3:4b"


# ==============================================================================
# 14. COMPLIANCE ANALYSIS (Section 15, 33)
# User: "Perform regulatory compliance audit against ISO 14224 standard."
# Expected: ComplianceAgent, qwen3:4b
# ==============================================================================
def test_14_compliance_analysis():
    query = "Perform regulatory compliance audit against ISO 14224 standard."
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.COMPLIANCE_ANALYSIS.value
    assert classification.agent == "compliance_agent"
    assert classification.recommended_model == "qwen3:4b"
    
    route = model_router.select(task_type="COMPLIANCE_ANALYSIS")
    assert route["selected_model"] == "qwen3:4b"


# ==============================================================================
# 15. RISK ANALYSIS (Section 15, 33)
# User: "Perform FMEA risk analysis and calculate risk priority numbers."
# Expected: RiskAgent, qwen3:4b
# ==============================================================================
def test_15_risk_analysis():
    query = "Perform FMEA risk analysis and calculate risk priority numbers."
    classification = task_classifier.classify(query)
    
    assert classification.task_type == TaskType.RISK_ANALYSIS.value
    assert classification.agent == "risk_agent"
    assert classification.recommended_model == "qwen3:4b"
    
    route = model_router.select(task_type="RISK_ANALYSIS")
    assert route["selected_model"] == "qwen3:4b"


# ==============================================================================
# 16. BOUNDED AGENT LOOP & STOP CONDITIONS (Section 23, 29)
# Verifies step count bounds (MAX_STEPS = 5) and early stop upon artifact validation
# ==============================================================================
def test_16_bounded_execution_rules():
    from agents.langgraph_agent import MAX_STEPS, should_continue, AgentState
    from langchain_core.messages import AIMessage
    
    assert MAX_STEPS == 5
    
    # State with step_count >= 5 must terminate immediately
    exhausted_state = {
        "messages": [AIMessage(content="Step 5 reached")],
        "task": "Perform maintenance analysis",
        "selected_model": "qwen3:4b",
        "step_count": 5,
        "state_status": "EXECUTING"
    }
    assert should_continue(exhausted_state) == "__end__"
    
    # State with validated artifact deliverable must stop immediately
    ai_msg_with_call = AIMessage(content="Tool called", tool_calls=[{"name": "create_excel", "args": {}, "id": "1"}])
    completed_state = {
        "messages": [ai_msg_with_call],
        "task": "Create Excel inspection report",
        "selected_model": "qwen2.5:1.5b",
        "step_count": 2,
        "state_status": "OBSERVING",
        "generated_files": [{"name": "test.xlsx", "type": "xlsx", "valid": True}]
    }
    assert should_continue(completed_state) == "__end__"
