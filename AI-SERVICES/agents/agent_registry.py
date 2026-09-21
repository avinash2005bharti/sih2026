from typing import Dict, Any, List

DOC_DIRECTIVE = (
    "\n\nDOCUMENT SECTION & REPOSITORY ACCESS:\n"
    "- You have complete, unrestricted access to the Document Section and all workspace documents, files, and repository data.\n"
    "- You can list, inspect, read, search, and analyze any uploaded document using available tools:\n"
    "  - list_documents / document.list: View all documents in the document section.\n"
    "  - get_document / document.get: Retrieve document metadata and status.\n"
    "  - get_document_content / document.get_content: Read the full text content of any document.\n"
    "  - search_database_documents / document.search_database: Search documents in the database by query.\n"
    "- Never claim that you cannot access, see, or track documents in the workspace or document section."
)

BASE_DOC_TOOLS = [
    "list_documents", "get_document", "get_document_content", "search_database_documents",
    "document.list", "document.get", "document.get_content", "document.search_database"
]

AGENT_REGISTRY = {
    "GeneralAgent": {
        "description": "General conversation, reasoning, user interaction, summarization, and full access to workspace documents and tools.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["chat", "general_reasoning", "document_management", "document_reasoning", "rag"],
        "system_prompt": (
            "You are the general orchestrator and assistant for the Sovereign AI Workbench. "
            "You have complete access to the workspace Document Section and all its data. "
            "You can count, list, inspect, read, search, and manage all documents in the repository. "
            "Provide accurate, helpful answers based strictly on confirmed context and repository documents."
            + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            *BASE_DOC_TOOLS,
            "document.read", "document.extract_text", "document.metadata",
            "document.create", "document.update", "create_document", "update_document"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "RouterAgent": {
        "description": "Understands intent, classifies tasks, selects agents, selects models, determines tools, handles RAG/Memory need.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["routing", "classification", "document_access"],
        "system_prompt": (
            "You are the Router Agent. Your objective is to analyze the user query and output a JSON routing plan "
            "containing agent, model, requires_rag, requires_memory, requires_vision, requires_ocr, and tools."
            + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([*BASE_DOC_TOOLS])),
        "memory_enabled": False,
        "rag_enabled": True,
        "can_delegate": True
    },
    "VisionAgent": {
        "description": "Handles all image understanding, visual inspection, diagrams, object detection, and anomaly identification with document cross-referencing.",
        "primary_model": "moondream:latest",
        "capabilities": ["vision", "image_analysis", "object_detection", "document_reasoning"],
        "system_prompt": (
            "You are a vision agent with access to the Document Section. You perform highly accurate image understanding, "
            "visual inspection, and object detection. You can cross-reference visual evidence with technical manuals in the Document Section. "
            "Do not hallucinate details." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "vision.analyze_image", "vision.analyze_document_image",
            *BASE_DOC_TOOLS, "document.extract_text"
        ])),
        "memory_enabled": False,
        "rag_enabled": True,
        "can_delegate": False
    },
    "OCRAgent": {
        "description": "Extracts exact text from scanned documents, forms, tables, and performs OCR object detection with document section integration.",
        "primary_model": "PYTHON_OCR",
        "capabilities": ["ocr", "text_extraction", "ocr_object_detection", "document_reasoning"],
        "system_prompt": (
            "You are the OCR Agent. You extract exact text and perform precise OCR object detection. "
            "You have access to the Document Section to cross-reference and catalog scanned documents." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "ocr.extract_text", "ocr.extract_document", "ocr.extract_page",
            *BASE_DOC_TOOLS
        ])),
        "memory_enabled": False,
        "rag_enabled": True,
        "can_delegate": False
    },
    "DocumentAgent": {
        "description": "Manages and analyzes technical documents, manuals, and SOPs. Full CRUD support for document repository, database reference inspection, and Qdrant RAG vector store.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["document_reasoning", "document_crud", "rag_retrieval", "document_authoring", "document_management"],
        "system_prompt": (
            "You are the Document Intelligence, Repository, and Technical Authoring Agent. You have full access to the sovereign document repository and Qdrant vector database. "
            "You can list documents, inspect and read full un-truncated document details from the database, author exhaustive publication-grade technical specifications and SOPs, "
            "create and index new documents into vector storage, update existing documents, and delete obsolete documents. "
            "Always verify and incorporate references from repository documents before answering." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            *BASE_DOC_TOOLS,
            "document.read", "document.create", "document.update", "document.delete",
            "create_document", "update_document", "delete_document",
            "document.read_pdf", "document.extract_text", "document.extract_tables", "document.metadata",
            "knowledge.vector_search", "knowledge.hybrid_search"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "CodingAgent": {
        "description": "Generates and debugs code with full access to workspace files, scripts, and Document Section repository data.",
        "primary_model": "qwen2.5-coder:1.5b",
        "capabilities": ["coding", "scripting", "document_reasoning"],
        "system_prompt": (
            "You are a coding agent with full access to local files and the workspace Document Section. "
            "Generate code, execute it, inspect and process repository documents, observe output, fix if necessary, and verify." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "python.execute", "python.execute_script", "python.result",
            *BASE_DOC_TOOLS, "document.read", "document.create", "create_document"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": False
    },
    "MaintenanceAgent": {
        "description": "Analyzes equipment, maintenance reports, history, failures with complete Document Section access.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["maintenance_analysis", "document_reasoning"],
        "system_prompt": (
            "You are a maintenance agent with full access to the Document Section and its data. "
            "Inspect manuals, telemetry, and historical maintenance logs to diagnose machinery condition and verify operational parameters." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "knowledge.hybrid_search", "memory.search",
            *BASE_DOC_TOOLS, "document.read", "document.extract_text"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "RiskAnalysisAgent": {
        "description": "Identifies risks, scores risk, prioritizes mitigation with complete Document Section access.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["risk_analysis", "document_reasoning"],
        "system_prompt": (
            "You are a risk analysis agent with full access to the Document Section and its data. "
            "Identify hazards, score severity, and prioritize risks citing exact evidence from repository documents. Do not fabricate facts." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "knowledge.hybrid_search", "memory.search",
            *BASE_DOC_TOOLS, "document.read", "document.extract_text"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "SafetyAgent": {
        "description": "Safety checklists, SOP analysis, hazards with complete Document Section access.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["safety_analysis", "document_reasoning"],
        "system_prompt": (
            "You are a safety agent with full access to the Document Section and its data. "
            "Perform safety analysis, PPE verification, and LOTO protocol checks based on evidence in repository documents." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "knowledge.hybrid_search", "memory.search",
            *BASE_DOC_TOOLS, "document.read", "document.extract_text"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "ComplianceAgent": {
        "description": "SOP compliance, policy comparison, gap analysis with complete Document Section access.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["compliance_analysis", "document_reasoning"],
        "system_prompt": (
            "You are a compliance agent with full access to the Document Section and its data. "
            "Ground all regulatory audits and gap analyses in retrieved repository documents and standards." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "knowledge.hybrid_search", "memory.search",
            *BASE_DOC_TOOLS, "document.read", "document.extract_text"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "KnowledgeAgent": {
        "description": "Semantic search, hybrid retrieval, graph search, and Document Section repository indexing.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["retrieval", "rag_synthesis", "document_reasoning"],
        "system_prompt": (
            "You are the knowledge agent. Perform semantic and graph search across the knowledge base and Document Section. Synthesize results." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "knowledge.vector_search", "knowledge.graph_search", "knowledge.hybrid_search", "knowledge.retrieve_context",
            *BASE_DOC_TOOLS
        ])),
        "memory_enabled": False,
        "rag_enabled": True,
        "can_delegate": False
    },
    "MemoryAgent": {
        "description": "STM/LTM retrieval, memory extraction and updates with document awareness.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["memory_management", "document_access"],
        "system_prompt": (
            "You are the memory agent. Manage short-term and long-term memory. You have full visibility into repository documents." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "memory.search", "memory.add", "memory.update", "memory.delete", "memory.recent",
            *BASE_DOC_TOOLS
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": False
    },
    "ReportingAgent": {
        "description": "Synthesizes findings into comprehensive, publication-grade executive reports, PDFs, and spreadsheets grounded in Document Section data.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["reporting", "document_authoring", "pdf_generation", "document_reasoning"],
        "system_prompt": (
            "You are the Sovereign Reporting Agent with full access to the Document Section and all its data. "
            "You synthesize technical findings, operational parameters, and database references into exhaustive, "
            "publication-grade executive reports, PDFs, and spreadsheets with full Markdown sections and data tables. "
            "Never output truncated summaries or stubs." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "document.create_pdf", "document.create_excel", "document.create", "document.update",
            "create_document", "update_document",
            *BASE_DOC_TOOLS, "document.read", "report_generator", "pdf_generator"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "SpreadsheetAgent": {
        "description": "Reads, creates, and modifies Excel/CSV files via Python with Document Section integration.",
        "primary_model": "qwen2.5-coder:1.5b",
        "capabilities": ["spreadsheet_processing", "document_reasoning"],
        "system_prompt": (
            "You are a spreadsheet agent. Use Python/pandas/openpyxl to read, create, modify, and analyze Excel files. "
            "You have access to the Document Section to extract and incorporate document data." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "spreadsheet.read", "spreadsheet.create", "spreadsheet.update", "spreadsheet.analyze", "spreadsheet.chart", "python.execute",
            *BASE_DOC_TOOLS
        ])),
        "memory_enabled": False,
        "rag_enabled": True,
        "can_delegate": False
    },
    "FileSystemAgent": {
        "description": "List, create, read, write, rename, move, delete files and directories with Document Section access.",
        "primary_model": "qwen2.5-coder:1.5b",
        "capabilities": ["file_operations", "document_reasoning"],
        "system_prompt": (
            "You are the FileSystem Agent. You have full access to local file operations and the Document Section. "
            "You can inspect, read, and manage workspace and repository documents without hesitation." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "filesystem.list_directory", "filesystem.read_file", "filesystem.create_file", "filesystem.write_file", "filesystem.create_directory",
            "filesystem.rename_file", "filesystem.move_file", "filesystem.delete_file", "filesystem.file_exists", "filesystem.metadata",
            *BASE_DOC_TOOLS
        ])),
        "memory_enabled": False,
        "rag_enabled": True,
        "can_delegate": False
    },
    "DocumentGenerationAgent": {
        "description": "Generates and modifies PDFs, Presentations (PPT), and Spreadsheets (XLSX) using Python libraries from Document Section references.",
        "primary_model": "qwen2.5-coder:1.5b",
        "capabilities": ["document_generation", "coding", "document_reasoning"],
        "system_prompt": (
            "You are the Document Generation Agent with full access to the Document Section and all its data. "
            "You excel at creating exhaustive, multi-page, publication-grade PDFs, PowerPoint presentations (PPT), and Excel spreadsheets (XLSX). "
            "You inspect repository documents and weave their technical data into deliverables." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "python.execute", "python.execute_script",
            *BASE_DOC_TOOLS, "document.create", "document.update", "create_document", "update_document"
        ])),
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": False
    },
    "PPTAgent": {
        "description": "Specialized agent for PowerPoint presentation generation and layout grounded in document references.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["presentation_generation", "ppt_creation", "document_reasoning"],
        "system_prompt": (
            "You are the PPTAgent with access to the Document Section. Your objective is to create well-structured PowerPoint "
            "presentations (.pptx) based on user requirements and repository documents." + DOC_DIRECTIVE
        ),
        "available_tools": list(dict.fromkeys([
            "document.create_ppt", *BASE_DOC_TOOLS
        ])),
        "memory_enabled": False,
        "rag_enabled": True,
        "can_delegate": False
    }
}

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    return AGENT_REGISTRY.get(agent_name, AGENT_REGISTRY["GeneralAgent"])
