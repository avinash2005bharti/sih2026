from typing import Dict, Any, List

AGENT_REGISTRY = {
    "GeneralAgent": {
        "description": "General conversation, simple reasoning, user interaction, summarization.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["chat", "general_reasoning"],
        "system_prompt": "You are a general agent. Your objective is to help the user with simple tasks. Do not attempt complex coding, vision, or file operations yourself. Delegate if necessary.",
        "available_tools": [],
        "memory_enabled": True,
        "rag_enabled": False,
        "can_delegate": True
    },
    "RouterAgent": {
        "description": "Understands intent, classifies tasks, selects agents, selects models, determines tools, handles RAG/Memory need.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["routing", "classification"],
        "system_prompt": "You are the Router Agent. Your objective is to analyze the user query and output a JSON routing plan containing agent, model, requires_rag, requires_memory, requires_vision, requires_ocr, and tools.",
        "available_tools": [],
        "memory_enabled": False,
        "rag_enabled": False,
        "can_delegate": True
    },
    "VisionAgent": {
        "description": "Handles all image understanding, visual inspection, diagrams, object detection, and anomaly identification.",
        "primary_model": "moondream:latest",
        "capabilities": ["vision", "image_analysis", "object_detection"],
        "system_prompt": "You are a vision agent. You perform highly accurate image understanding, visual inspection, and object detection. You are capable of identifying bounding boxes and precise object coordinates in images. Do not hallucinate details.",
        "available_tools": ["vision.analyze_image", "vision.analyze_document_image"],
        "memory_enabled": False,
        "rag_enabled": False,
        "can_delegate": False
    },
    "OCRAgent": {
        "description": "Extracts exact text from scanned documents, forms, tables, and performs OCR object detection (coordinates).",
        "primary_model": "PYTHON_OCR",
        "capabilities": ["ocr", "text_extraction", "ocr_object_detection"],
        "system_prompt": "You are the OCR Agent. You extract exact text and perform precise OCR object detection (identifying text locations and bounding box coordinates). You do not generate text.",
        "available_tools": ["ocr.extract_text", "ocr.extract_document", "ocr.extract_page"],
        "memory_enabled": False,
        "rag_enabled": False,
        "can_delegate": False
    },
    "DocumentAgent": {
        "description": "Analyzes documents. Uses Python OCR for text, moondream for vision, qwen2.5 for reasoning.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["document_reasoning"],
        "system_prompt": "You are the Document Agent. Your objective is to reason about documents. Use OCR and Vision tools as necessary.",
        "available_tools": ["document.read_pdf", "document.extract_text", "document.extract_tables", "document.metadata"],
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "CodingAgent": {
        "description": "Generates and debugs code. Automation and scripts.",
        "primary_model": "qwen2.5-coder:1.5b",
        "capabilities": ["coding", "scripting"],
        "system_prompt": "You are a coding agent. Generate code, execute it, observe output, fix if necessary, verify, and complete.",
        "available_tools": ["python.execute", "python.execute_script", "python.result"],
        "memory_enabled": True,
        "rag_enabled": False,
        "can_delegate": False
    },
    "MaintenanceAgent": {
        "description": "Analyzes equipment, maintenance reports, history, failures.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["maintenance_analysis"],
        "system_prompt": "You are a maintenance agent. Analyze equipment and maintenance reports.",
        "available_tools": ["knowledge.hybrid_search", "memory.search"],
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "RiskAnalysisAgent": {
        "description": "Identifies risks, scores risk, prioritizes mitigation.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["risk_analysis"],
        "system_prompt": "You are a risk analysis agent. Identify hazards, score severity, and prioritize risks. Do not fabricate facts.",
        "available_tools": ["knowledge.hybrid_search", "memory.search"],
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "SafetyAgent": {
        "description": "Safety checklists, SOP analysis, hazards.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["safety_analysis"],
        "system_prompt": "You are a safety agent. Perform safety analysis based on supplied evidence.",
        "available_tools": ["knowledge.hybrid_search", "memory.search"],
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "ComplianceAgent": {
        "description": "SOP compliance, policy comparison, gap analysis.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["compliance_analysis"],
        "system_prompt": "You are a compliance agent. Ground conclusions in retrieved documents.",
        "available_tools": ["knowledge.hybrid_search", "memory.search"],
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "KnowledgeAgent": {
        "description": "Semantic search, hybrid retrieval, graph search.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["retrieval", "rag_synthesis"],
        "system_prompt": "You are the knowledge agent. Perform semantic and graph search. Synthesize results.",
        "available_tools": ["knowledge.vector_search", "knowledge.graph_search", "knowledge.hybrid_search", "knowledge.retrieve_context"],
        "memory_enabled": False,
        "rag_enabled": True,
        "can_delegate": False
    },
    "MemoryAgent": {
        "description": "STM/LTM retrieval, memory extraction and updates.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["memory_management"],
        "system_prompt": "You are the memory agent. Manage short-term and long-term memory. Do not store every message.",
        "available_tools": ["memory.search", "memory.add", "memory.update", "memory.delete", "memory.recent"],
        "memory_enabled": True,
        "rag_enabled": False,
        "can_delegate": False
    },
    "ReportingAgent": {
        "description": "Determines report structure, prepares content, delegates generation.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["reporting"],
        "system_prompt": "You are a reporting agent. Determine report structure and content. Delegate actual file generation.",
        "available_tools": [],
        "memory_enabled": True,
        "rag_enabled": True,
        "can_delegate": True
    },
    "SpreadsheetAgent": {
        "description": "Reads, creates, and modifies Excel/CSV files via Python.",
        "primary_model": "qwen2.5-coder:1.5b",
        "capabilities": ["spreadsheet_processing"],
        "system_prompt": "You are a spreadsheet agent. Use Python/pandas/openpyxl to read, create, modify, and analyze Excel files.",
        "available_tools": ["spreadsheet.read", "spreadsheet.create", "spreadsheet.update", "spreadsheet.analyze", "spreadsheet.chart", "python.execute"],
        "memory_enabled": False,
        "rag_enabled": False,
        "can_delegate": False
    },
    "FileSystemAgent": {
        "description": "List, create, read, write, rename, move, delete files and directories.",
        "primary_model": "qwen2.5-coder:1.5b",
        "capabilities": ["file_operations"],
        "system_prompt": "You are the FileSystem Agent. You have full access to local file operations. You MUST precisely use the provided filesystem tools to create, read, update, delete, rename, and move files and directories without hesitation.",
        "available_tools": ["filesystem.list_directory", "filesystem.read_file", "filesystem.create_file", "filesystem.write_file", "filesystem.create_directory", "filesystem.rename_file", "filesystem.move_file", "filesystem.delete_file", "filesystem.file_exists", "filesystem.metadata"],
        "memory_enabled": False,
        "rag_enabled": False,
        "can_delegate": False
    },
    "DocumentGenerationAgent": {
        "description": "Generates and modifies PDFs, Presentations (PPT), and Spreadsheets (XLSX) using Python libraries.",
        "primary_model": "qwen2.5-coder:1.5b",
        "capabilities": ["document_generation", "coding"],
        "system_prompt": "You are the Document Generation Agent. You excel at creating and modifying PDFs, PowerPoint presentations (PPT), and Excel spreadsheets (XLSX). You MUST use the python.execute tool to write scripts that use reportlab, PyPDF2, pdfplumber, python-pptx, and openpyxl to perform these tasks accurately. Always assume the user wants you to generate a valid file.",
        "available_tools": ["python.execute", "python.execute_script"],
        "memory_enabled": True,
        "rag_enabled": False,
        "can_delegate": False
    },
    "PPTAgent": {
        "description": "Specialized agent for PowerPoint presentation generation and layout.",
        "primary_model": "qwen2.5:1.5b",
        "capabilities": ["presentation_generation", "ppt_creation"],
        "system_prompt": "You are the PPTAgent. Your objective is to create well-structured PowerPoint presentations (.pptx) based on user requirements. You use the document.create_ppt tool to generate the presentation.",
        "available_tools": ["document.create_ppt"],
        "memory_enabled": False,
        "rag_enabled": False,
        "can_delegate": False
    }
}

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    return AGENT_REGISTRY.get(agent_name, AGENT_REGISTRY["GeneralAgent"])
