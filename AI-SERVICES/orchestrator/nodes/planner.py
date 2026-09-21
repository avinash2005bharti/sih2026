"""
Planner Node for Sovereign Agentic Orchestrator.
Decomposes complex industrial goals into actionable, ordered execution steps.
Uses local SLM structured JSON output with deterministic heuristic fallback.
Planner model: llama3.2:1b (via model_registry with fallbacks).
"""

import json
from typing import List, Dict, Any
from orchestrator.state import AgenticState, StepPlan
from llm.ollama_client import ollama_client
from llm.model_registry import model_registry
from tools.tool_registry import central_tool_registry
from core.logging import logger


def build_planner_prompt() -> str:
    registered_tools = central_tool_registry.list_tools()
    tools_list_str = "\n".join([f"- '{t}'" for t in registered_tools])

    return f"""You are the Sovereign Industrial Task Planner.
Break the user's objective into 1 to 5 logical sequential execution steps.

Available specialist agents:
- 'document': document analysis, text extraction, inspecting database documents, structured ingestion.
- 'risk': industrial hazard analysis, failure risk quantification. Has full access to Document Section.
- 'compliance': ISO standards, regulatory verification, audit checklists. Has full access to Document Section.
- 'safety': OSHA hazard analysis, safety protocols, worker protection. Has full access to Document Section.
- 'maintenance': equipment telemetry, failure codes, sensor diagnosis. Has full access to Document Section.
- 'coding': python script calculations, automation, data transformation, and file/document inspection.
- 'reporting': synthesizing findings, creating executive reports (PDF/DOCX/MD) grounded in document data.
- 'general': general engineering Q&A, explanations, full document section visibility.
- 'vision': visual inspection, defect detection.

NOTE ON DOCUMENT SECTION ACCESS:
All specialist agents have complete access to the workspace Document Section and its data.
Available document section tools include:
- 'list_documents': List all documents in the Document Section repository.
- 'get_document': Retrieve metadata and indexing status for a document.
- 'get_document_content': Retrieve full, un-truncated content and technical data of a document.
- 'search_database_documents': Search for keywords or clauses across all documents.
- 'create_document': Create and index a document into the Document Section.
- 'update_document': Update or append data to a document in the Document Section.
- 'document_parser': Multi-format file parsing.
- 'rag_search': Vector similarity search over indexed chunks.

Available Registered Tools (ONLY select from this list):
{tools_list_str}

CRITICAL PLANNING GUIDELINES FOR DOCUMENTS:
- When the user asks to inspect, view, read, list, or get documents (e.g. "give me any document", "show me the document", "read document", "list documents"):
  * Do NOT generate or compile new reports or files. Do NOT use 'report_generator', 'pdf_generator', or 'docx_generator'.
  * Plan inspection and retrieval steps using 'get_document_content', 'list_documents', or 'read_file'.
- When the user explicitly asks to CREATE, AUTHOR, or GENERATE a document, SOP, or PDF deliverable:
  * Step 1: Must retrieve source document details and references using 'get_document_content', 'rag_search', or 'search_database_documents'.
  * Step 2: Must synthesize complete technical specifications, operating parameters, and sequential procedures.
  * Step 3: Must compile and generate the deliverable using 'pdf_generator' or 'report_generator'.

Output strictly valid JSON with this exact schema:
{{
  "goal": "Description of the goal",
  "steps": [
    {{
      "id": 1,
      "action": "Short action name",
      "tool": "registered_tool_name",
      "target_agent": "specialist_agent_name",
      "description": "Specific action description",
      "expected_outcome": "what this step should produce"
    }}
  ]
}}"""


class PlannerNode:
    """Plans execution steps for the agentic workflow using specialist SLM."""

    async def execute(self, state: AgenticState) -> AgenticState:
        logger.info(f"[PLANNER] Planning for task: '{state.user_query[:80]}'")
        state.status = "planning"

        q = state.user_query.lower()
        has_inspect = any(w in q for w in ["get", "give", "show", "read", "view", "display", "fetch", "open", "find", "what is in", "contents", "what document", "which document", "any document", "list document"])
        has_create = any(w in q for w in ["create", "generate", "author", "write", "draft", "make", "compile", "build", "produce", "new"])

        # If user is asking to retrieve, view, or inspect a document without asking to generate a new deliverable:
        if has_inspect and not has_create and any(w in q for w in ["document", "doc", "pdf", "file", "manual", "sop", "report"]):
            state.plan = [
                StepPlan(
                    step_number=1,
                    title="Retrieve & Inspect Document",
                    description="Locate and inspect the text content of the requested document from repository or uploads.",
                    target_agent="document",
                    required_tools=["get_document_content"],
                    expected_outcome="Accurate content and metadata of the requested document, or verification that 0 documents exist"
                ),
                StepPlan(
                    step_number=2,
                    title="Present Document Information",
                    description="Accurately summarize or present the retrieved document content to the user without hallucinating SOP manuals.",
                    target_agent="document",
                    required_tools=[],
                    expected_outcome="Accurate, factual response based strictly on actual documents"
                )
            ]
            logger.info("[PLANNER] Generated deterministic document inspection steps")
            return state

        model = model_registry.get_model("planner")
        valid_tools = set(central_tool_registry.list_tools())
        prompt = build_planner_prompt()

        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Create an execution plan for: {state.user_query}"}
            ]

            result = await ollama_client.chat_json(model=model, messages=messages)

            # Accept both {"steps": [...]} and {"plan": [...]}
            raw_steps = result.get("steps") or result.get("plan") or []

            if isinstance(raw_steps, list) and len(raw_steps) > 0:
                steps = []
                for idx, p in enumerate(raw_steps):
                    tool_candidate = p.get("tool") or (p.get("required_tools", [None])[0] if p.get("required_tools") else None)
                    tools = [tool_candidate] if tool_candidate and tool_candidate in valid_tools else []
                    if "required_tools" in p and isinstance(p["required_tools"], list):
                        tools = [t for t in p["required_tools"] if t in valid_tools]

                    step = StepPlan(
                        step_number=p.get("id") or p.get("step_number") or (idx + 1),
                        title=p.get("action") or p.get("title") or f"Step {idx + 1}",
                        description=p.get("description", ""),
                        target_agent=p.get("target_agent", "general"),
                        required_tools=tools,
                        expected_outcome=p.get("expected_outcome", ""),
                        status="pending"
                    )
                    steps.append(step)

                state.plan = steps
                logger.info(f"[PLANNER] Generated {len(state.plan)} steps via SLM ({model})")
                return state

        except Exception as e:
            logger.warning(f"[PLANNER] SLM generation failed ({e}), using deterministic heuristic fallback planner")

        # Deterministic heuristic fallback planner
        state.plan = self._fallback_plan(state.user_query)
        logger.info(f"[PLANNER] Generated {len(state.plan)} deterministic fallback steps")
        return state

    def _fallback_plan(self, query: str) -> List[StepPlan]:
        """Creates a reliable fallback plan when LLM is offline or busy."""
        q = query.lower()

        # Dedicated branch for inspection reports, scanned documents, and Word approval note drafting
        if any(w in q for w in ["inspection", "scanned", "approval note", "clearance note"]) and any(w in q for w in ["word", "docx", "draft", "note", "report"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Extract Key Findings from Scanned Inspection Report",
                    description="Perform OCR and document parsing on the scanned inspection report to extract all telemetry readings, bearing temperatures, vibration levels, and physical defect notes.",
                    target_agent="document",
                    required_tools=["document_parser", "ocr"],
                    expected_outcome="Key technical findings, sensor telemetry, and defect logs extracted from scanned report"
                ),
                StepPlan(
                    step_number=2,
                    title="Evaluate Engineering Tolerances & Clearance Criteria",
                    description="Cross-reference extracted inspection values against ISO mechanical standards and operational safety limits to formulate clearance conditions.",
                    target_agent="maintenance",
                    required_tools=[],
                    expected_outcome="Detailed technical evaluation, deviation analysis, and maintenance recommendations"
                ),
                StepPlan(
                    step_number=3,
                    title="Draft Formal Approval Note as Word File (.docx)",
                    description="Synthesize an executive-ready Microsoft Word (.docx) approval note detailing equipment status, findings, mandatory remedial items, and engineering sign-off.",
                    target_agent="reporting",
                    required_tools=["docx_generator"],
                    expected_outcome="Formal Approval Note document (.docx) saved to reports repository"
                )
            ]

        # Dedicated branch for document retrieval, inspection, and viewing (NOT generation)
        has_inspect = any(w in q for w in ["get", "give", "show", "read", "view", "display", "fetch", "open", "find", "what is in", "contents", "what document", "which document", "any document", "list document"])
        has_create = any(w in q for w in ["create", "generate", "author", "write", "draft", "make", "compile", "build", "produce", "new"])

        if has_inspect and not has_create and any(w in q for w in ["document", "doc", "pdf", "file", "manual", "sop", "report"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Retrieve & Inspect Document",
                    description="Locate and inspect the text content of the requested document from repository or uploads.",
                    target_agent="document",
                    required_tools=["read_file"],
                    expected_outcome="Accurate content and metadata of the requested document, or verification that 0 documents exist"
                ),
                StepPlan(
                    step_number=2,
                    title="Present Document Information",
                    description="Accurately summarize or present the retrieved document content to the user without hallucinating SOP manuals.",
                    target_agent="document",
                    required_tools=[],
                    expected_outcome="Accurate, factual response based strictly on actual documents"
                )
            ]

        # Dedicated branch for document authoring, SOP generation, PDF creation, and deliverable compilation
        if has_create and any(w in q for w in ["pdf", "document", "sop", "manual", "guide", "procedure", "specification", "maintenance plan", "word", "docx"]) and not any(w in q for w in ["csv", "spreadsheet", "xlsx"]):
            is_word = any(w in q for w in ["word", "docx", "approval note"])
            is_pdf = "pdf" in q and not is_word
            doc_tool = "docx_generator" if is_word else ("pdf_generator" if is_pdf else "report_generator")
            return [
                StepPlan(
                    step_number=1,
                    title="Retrieve Source Document & Database References",
                    description="Extract full technical specifications, operating limits, sequential procedures, and safety rules from uploaded and database documents.",
                    target_agent="document",
                    required_tools=["rag_search"],
                    expected_outcome="Full technical parameters, operational ranges, and reference citations from database documents"
                ),
                StepPlan(
                    step_number=2,
                    title="Synthesize Comprehensive Technical Specifications",
                    description="Formulate complete sequential operating procedures, technical parameters, hazard controls, and validation checklists based on retrieved evidence.",
                    target_agent="maintenance" if any(w in q for w in ["maintenance", "turbine", "motor", "pump", "telemetry"]) else "compliance",
                    required_tools=[],
                    expected_outcome="Exhaustive draft with complete sections, step-by-step instructions, and data tables"
                ),
                StepPlan(
                    step_number=3,
                    title="Generate Production-Ready Deliverable Document",
                    description="Compile and format the full exhaustive document into the requested deliverable without abbreviation or truncation.",
                    target_agent="reporting",
                    required_tools=[doc_tool],
                    expected_outcome="Formatted, publication-grade document file artifact"
                )
            ]
        elif any(w in q for w in ["csv", "spreadsheet", "xlsx", "telemetry", "vibration", "sensor", "metric"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Read & Inspect Spreadsheet",
                    description="Analyze spreadsheet columns, row count, and statistical distributions.",
                    target_agent="maintenance",
                    required_tools=["spreadsheet_reader"],
                    expected_outcome="Summary statistics and data rows"
                ),
                StepPlan(
                    step_number=2,
                    title="Synthesize Technical Report",
                    description="Compile findings into a structured industrial diagnostic report.",
                    target_agent="reporting",
                    required_tools=["report_generator"],
                    expected_outcome="Final markdown diagnostic report"
                )
            ]
        elif any(w in q for w in ["code", "python", "script", "calculate", "automation"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Execute Computational Logic",
                    description="Run Python code in the sandbox to process the requested logic.",
                    target_agent="coding",
                    required_tools=["python_executor"],
                    expected_outcome="Execution output and calculations"
                ),
                StepPlan(
                    step_number=2,
                    title="Verify and Format Results",
                    description="Verify execution correctness and format final outcome.",
                    target_agent="reporting",
                    required_tools=["report_generator"],
                    expected_outcome="Verified solution"
                )
            ]
        elif any(w in q for w in ["hazard", "safety", "incident", "osha", "injury", "ppe"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Assess Safety Hazards & Evidence",
                    description="Identify hazards, evaluate OSHA / safety protocols, and categorize risk levels.",
                    target_agent="safety",
                    required_tools=["rag_search"],
                    expected_outcome="Hazard identification and protocol mapping"
                ),
                StepPlan(
                    step_number=2,
                    title="Generate Safety Action Plan",
                    description="Draft corrective actions, preventative measures, and compliance guidance.",
                    target_agent="compliance",
                    required_tools=["report_generator"],
                    expected_outcome="Safety action plan"
                )
            ]
        elif any(w in q for w in ["risk", "fmea", "severity", "failure"]):
            return [
                StepPlan(
                    step_number=1,
                    title="Retrieve Risk Evidence",
                    description="Retrieve technical specifications, incident histories, and operating limits.",
                    target_agent="risk",
                    required_tools=["rag_search"],
                    expected_outcome="Ground-truth technical evidence from knowledge base"
                ),
                StepPlan(
                    step_number=2,
                    title="Perform Quantitative Risk Analysis",
                    description="Quantify failure probabilities, severity scores, and specify mitigations.",
                    target_agent="risk",
                    required_tools=["report_generator"],
                    expected_outcome="Quantified risk assessment matrix"
                )
            ]
        else:
            return [
                StepPlan(
                    step_number=1,
                    title="Retrieve Relevant Knowledge",
                    description="Search indexed sovereign documentation and technical manual chunks.",
                    target_agent="document",
                    required_tools=["rag_search"],
                    expected_outcome="Relevant technical context and citations"
                ),
                StepPlan(
                    step_number=2,
                    title="Synthesize Findings",
                    description="Synthesize findings and deliver actionable recommendations.",
                    target_agent="reporting",
                    required_tools=[],
                    expected_outcome="Comprehensive final answer with evidence"
                )
            ]

