import json
import re
from typing import Any, Dict
from core.config import settings
from core.logging import logger
from llm.ollama_client import ollama_client
from orchestrator.state import WorkbenchState, TaskContract

async def analyze_intent_node(state: WorkbenchState) -> Dict[str, Any]:
    """
    Classify request, determine complexity, and construct the Task Contract with Acceptance Criteria.
    """
    req = state["user_request"]
    lower_req = req.lower()

    # Heuristic fast check for complex file/tool generation requests
    task_triggers = ["create", "generate", "pdf", "excel", "xlsx", "docx", "analyze image", "tracker", "report", "script", "fmea", "sop", "inspect"]
    is_complex = any(k in lower_req for k in task_triggers)

    acceptance_criteria = []
    required_outputs = []
    required_tools = []

    if "pdf" in lower_req or (any(act in lower_req for act in ["create", "generate", "build", "produce", "export"]) and "report" in lower_req):
        is_complex = True
        required_outputs.append("PDF Report Artifact")
        required_tools.append("pdf_creator")
        acceptance_criteria.extend([
            "PDF file exists on disk and is non-empty",
            "PDF structure parsed successfully with no corrupt headers",
            "No blank pages detected",
            "Executive summary and equipment metrics included",
            "Risk assessment and recommendations present",
            "No unrendered placeholder strings ([Insert ...])"
        ])

    if "excel" in lower_req or "xlsx" in lower_req or "tracker" in lower_req:
        is_complex = True
        required_outputs.append("Excel (.xlsx) Tracker")
        required_tools.append("xlsx_creator")
        acceptance_criteria.extend([
            "Workbook file exists and opens cleanly with openpyxl",
            "Sheet and column headers match specification",
            "Non-empty data records present",
            "No broken formula reference codes (#REF!, #VALUE!)"
        ])

    if "image" in lower_req or "diagram" in lower_req or "p&id" in lower_req:
        is_complex = True
        required_outputs.append("Visual Telemetry Inspection")
        required_tools.append("image_analyzer")
        acceptance_criteria.append("Visual observations and exact component identifiers identified")

    if not acceptance_criteria:
        acceptance_criteria.append("Answer is factually grounded and directly addresses user inquiry.")

    contract = TaskContract(
        objective=req,
        required_outputs=required_outputs,
        constraints=["100% on-premise execution", "zero data egress", "mandatory artifact validation"],
        required_tools=required_tools,
        acceptance_criteria=acceptance_criteria
    )

    reasoning_traces = state.get("reasoning_traces", [])
    reasoning_traces.append({
        "title": "Intent & Task Contract Established",
        "details": f"Classified as {'Multi-Step Industrial Task' if is_complex else 'Direct Conversational Query'}. Acceptance criteria initialized.",
        "status": "verified"
    })

    return {
        "is_complex_task": is_complex,
        "task_contract": contract.model_dump(),
        "reasoning_traces": reasoning_traces,
        "status": "planning" if is_complex else "executing"
    }
