"""
Intelligent SLM Model Router and Intent Classifier for Sovereign AI Workbench.

Two-Tier Routing:
1. High-speed deterministic keyword/rule routing (zero LLM inference overhead on CPU).
2. Structured JSON LLM router (qwen3:0.6b / qwen2.5:0.5b) for ambiguous queries.

Returns structured routing schema:
{
  "intent": "...",
  "agent": "...",
  "requires_rag": true,
  "requires_document": false,
  "requires_vision": false,
  "requires_code": false,
  "tools": [],
  "confidence": 0.0
}
"""

import json
import re
from typing import Dict, Any, Optional, List
from core.config import settings
from core.logging import logger
from llm.model_registry import model_registry


SUPPORTED_INTENTS = [
    "general",
    "document_analysis",
    "document_creation",
    "risk_analysis",
    "compliance",
    "maintenance",
    "safety",
    "coding",
    "data_analysis",
    "report_generation",
    "image_analysis",
    "rag_question",
    "file_operation"
]

INTENT_TO_AGENT = {
    "general": "general",
    "document_analysis": "document_agent",
    "document_creation": "reporting_agent",
    "risk_analysis": "risk_agent",
    "compliance": "compliance_agent",
    "maintenance": "maintenance_agent",
    "safety": "safety_agent",
    "coding": "code_agent",
    "data_analysis": "code_agent",
    "report_generation": "reporting_agent",
    "image_analysis": "vision_agent",
    "rag_question": "document_agent",
    "file_operation": "filesystem_agent",
}

INTENT_TOOLS = {
    "general": [],
    "document_analysis": ["rag_search", "document_parser", "qdrant_search"],
    "document_creation": ["pdf_generator", "docx_generator", "spreadsheet_writer"],
    "risk_analysis": ["rag_search", "document_parser"],
    "compliance": ["rag_search", "document_parser"],
    "maintenance": ["rag_search", "document_parser", "spreadsheet_reader"],
    "safety": ["rag_search", "document_parser"],
    "coding": ["python_executor", "code_executor"],
    "data_analysis": ["spreadsheet_reader", "python_executor", "spreadsheet_writer"],
    "report_generation": ["report_generator", "pdf_generator", "docx_generator"],
    "image_analysis": ["ocr", "image_analyzer"],
    "rag_question": ["rag_search", "qdrant_search"],
    "file_operation": ["file_reader", "file_writer"],
}


class ModelRouter:
    """Routes tasks to appropriate SLM specialists with structured intent output."""

    def __init__(self):
        self.supported_intents = list(SUPPORTED_INTENTS)

    def rule_based_route(self, message: str, has_images: bool = False) -> Optional[Dict[str, Any]]:
        """
        Deterministic high-speed keyword routing.
        Handles clear deterministic patterns without calling any LLM.
        """
        text = (message or "").lower().strip()
        if not text and not has_images:
            return {
                "intent": "general",
                "agent": "general",
                "requires_rag": False,
                "requires_document": False,
                "requires_vision": False,
                "requires_code": False,
                "tools": [],
                "confidence": 1.0
            }

        # 1. Vision / Image requests
        if has_images or any(k in text for k in ["inspect image", "visual inspection", "in this photo", "picture attached", "ocr this", "extract text from image"]):
            return {
                "intent": "image_analysis",
                "agent": "vision_agent",
                "requires_rag": False,
                "requires_document": False,
                "requires_vision": True,
                "requires_code": False,
                "tools": ["ocr", "image_analyzer"],
                "confidence": 0.98
            }

        is_doc = any(k in text for k in ["pdf", "document", "manual", "sop", "report", "policy", "specification"])

        # 2. Risk analysis
        if any(k in text for k in ["risk", "hazard", "severity", "fmea", "mitigation", "hazard identification"]):
            return {
                "intent": "risk_analysis",
                "agent": "risk_agent",
                "requires_rag": is_doc,
                "requires_document": is_doc,
                "requires_vision": False,
                "requires_code": False,
                "tools": ["rag_search", "document_parser"] if is_doc else [],
                "confidence": 0.95
            }

        # 3. Compliance analysis
        if any(k in text for k in ["compliance", "comply", "audit", "violation", "iso standard", "osha compliance", "against sop"]):
            return {
                "intent": "compliance",
                "agent": "compliance_agent",
                "requires_rag": True,
                "requires_document": True,
                "requires_vision": False,
                "requires_code": False,
                "tools": ["rag_search", "document_parser"],
                "confidence": 0.95
            }

        # 4. Plant Safety
        if any(k in text for k in ["safety", "unsafe", "ppe", "worker safety", "lockout tagout", "safety protocol", "incident report"]):
            return {
                "intent": "safety",
                "agent": "safety_agent",
                "requires_rag": is_doc,
                "requires_document": is_doc,
                "requires_vision": False,
                "requires_code": False,
                "tools": ["rag_search", "document_parser"] if is_doc else [],
                "confidence": 0.94
            }

        # 5. Maintenance / Telemetry
        if any(k in text for k in ["maintenance", "vibration", "bearing", "temperature", "telemetry", "breakdown", "equipment failure", "sensor"]):
            return {
                "intent": "maintenance",
                "agent": "maintenance_agent",
                "requires_rag": is_doc,
                "requires_document": is_doc,
                "requires_vision": False,
                "requires_code": False,
                "tools": ["rag_search", "document_parser", "spreadsheet_reader"] if is_doc else ["spreadsheet_reader"],
                "confidence": 0.93
            }

        # 6. Data Analysis / Spreadsheet
        if any(k in text for k in ["xlsx", "csv", "excel", "spreadsheet", "calculate", "average", "column", "sum rows", "filter data"]):
            return {
                "intent": "data_analysis",
                "agent": "code_agent",
                "requires_rag": False,
                "requires_document": False,
                "requires_vision": False,
                "requires_code": True,
                "tools": ["spreadsheet_reader", "python_executor", "spreadsheet_writer"],
                "confidence": 0.95
            }

        # 7. Document Creation / Modification / Reporting
        if any(k in text for k in [
            "create report", "generate report", "create pdf", "generate pdf", "make docx", "generate docx",
            "create excel", "export to excel", "generate document", "create document", "modify document",
            "update document", "edit document", "modify it with instructed data", "patch document",
            "add to document", "write document", "modify pdf"
        ]):
            return {
                "intent": "document_creation",
                "agent": "document_agent",
                "requires_rag": False,
                "requires_document": True,
                "requires_vision": False,
                "requires_code": True,
                "tools": ["create_document", "update_document", "create_pdf", "create_excel", "create_file", "patch_file"],
                "confidence": 0.98
            }

        # 8. File Operations
        if any(k in text for k in ["create folder", "mkdir", "delete file", "move file", "rename file", "list files", "write file", "save file", "file operation"]):
            return {
                "intent": "file_operation",
                "agent": "filesystem_agent",
                "requires_rag": False,
                "requires_document": False,
                "requires_vision": False,
                "requires_code": True,
                "tools": ["file_reader", "file_writer"],
                "confidence": 0.96
            }

        # 9. Coding / Scripting
        if any(k in text for k in ["code", "python", "javascript", "script", "debug", "function", "class", "algorithm"]):
            return {
                "intent": "coding",
                "agent": "code_agent",
                "requires_rag": False,
                "requires_document": False,
                "requires_vision": False,
                "requires_code": True,
                "tools": ["python_executor", "code_executor"],
                "confidence": 0.94
            }

        # 10. Document Repository / Count / Inventory
        if any(k in text for k in [
            "how many document", "how many documents", "count document", "count documents",
            "number of documents", "what documents", "which documents", "my documents",
            "document section", "document sections", "in document section", "in my document",
            "list documents", "show documents", "all documents", "uploaded documents"
        ]):
            return {
                "intent": "document_analysis",
                "agent": "document_agent",
                "requires_rag": False,
                "requires_document": True,
                "requires_vision": False,
                "requires_code": False,
                "tools": ["list_documents", "get_document"],
                "confidence": 0.98
            }

        # 11. Document Analysis / Summary
        if is_doc and any(k in text for k in ["summarize", "summarise", "extract", "what does the doc say", "read the manual", "search doc"]):
            return {
                "intent": "document_analysis",
                "agent": "document_agent",
                "requires_rag": True,
                "requires_document": True,
                "requires_vision": False,
                "requires_code": False,
                "tools": ["rag_search", "document_parser", "qdrant_search"],
                "confidence": 0.92
            }

        # 11. Question answering / Knowledge search
        if any(k in text for k in ["what is", "how do i", "explain", "why does", "according to"]):
            if is_doc or any(k in text for k in ["policy", "sop", "guideline", "manual", "standard"]):
                return {
                    "intent": "rag_question",
                    "agent": "document_agent",
                    "requires_rag": True,
                    "requires_document": True,
                    "requires_vision": False,
                    "requires_code": False,
                    "tools": ["rag_search", "qdrant_search"],
                    "confidence": 0.90
                }

        # If simple greeting or general talk
        if any(text == g or text.startswith(g + " ") for g in ["hi", "hello", "hey", "good morning", "good evening", "who are you", "what can you do"]):
            return {
                "intent": "general",
                "agent": "general",
                "requires_rag": False,
                "requires_document": False,
                "requires_vision": False,
                "requires_code": False,
                "tools": [],
                "confidence": 0.99
            }

        # Unmatched / ambiguous
        return None

    async def route_request(self, message: str, has_image: bool = False, file_type: Optional[str] = None) -> Dict[str, Any]:
        """Alias for route_async accepting both has_image and has_images."""
        return await self.route_async(message, has_images=has_image)

    async def route_async(self, message: str, has_images: bool = False) -> Dict[str, Any]:
        """
        Route request: uses rule-based routing first, falls back to LLM router for ambiguous requests.
        Guarantees structured JSON output schema.
        """
        # Phase 1: Rule-based routing
        rule_result = self.rule_based_route(message, has_images=has_images)
        if rule_result:
            logger.info(
                f"[ROUTER] Deterministic rule matched: intent='{rule_result['intent']}' agent='{rule_result['agent']}' (conf={rule_result['confidence']:.2f})"
            )
            return rule_result

        # Phase 2: LLM Router fallback
        router_model = model_registry.get_model("router")
        logger.info(f"[ROUTER] Ambiguous query. Calling router model '{router_model}' for structured JSON intent classification.")

        system_prompt = (
            "You are the Sovereign Request Router. Analyze the user request and classify its intent.\n"
            "Supported intents: general, document_analysis, document_creation, risk_analysis, compliance, maintenance, "
            "safety, coding, data_analysis, report_generation, image_analysis, rag_question, file_operation.\n"
            "Return ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "intent": "one of the supported intents",\n'
            '  "agent": "recommended specialist agent",\n'
            '  "requires_rag": true/false,\n'
            '  "requires_document": true/false,\n'
            '  "requires_vision": true/false,\n'
            '  "requires_code": true/false,\n'
            '  "tools": ["list of tools if needed"],\n'
            '  "confidence": 0.0 to 1.0\n'
            "}"
        )

        try:
            from llm.ollama_client import ollama_client
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            parsed = await ollama_client.chat_json(model=router_model, messages=messages)
            intent = parsed.get("intent", "general").lower().strip()
            if intent not in SUPPORTED_INTENTS:
                intent = "general"

            agent = parsed.get("agent") or INTENT_TO_AGENT.get(intent, "general")
            return {
                "intent": intent,
                "agent": agent,
                "requires_rag": bool(parsed.get("requires_rag", False)),
                "requires_document": bool(parsed.get("requires_document", False)),
                "requires_vision": bool(parsed.get("requires_vision", False)),
                "requires_code": bool(parsed.get("requires_code", False)),
                "tools": parsed.get("tools") or INTENT_TOOLS.get(intent, []),
                "confidence": float(parsed.get("confidence", 0.85))
            }
        except Exception as e:
            logger.warning(f"[ROUTER] LLM routing failed: {e}. Defaulting to general intent.")
            return {
                "intent": "general",
                "agent": "general",
                "requires_rag": False,
                "requires_document": False,
                "requires_vision": False,
                "requires_code": False,
                "tools": [],
                "confidence": 0.50
            }

    def route(self, message: str, task_type: str = "auto", preferred_model: Optional[str] = None) -> str:
        """Backward-compatible synchronous method returning the model name."""
        if preferred_model and preferred_model != "auto":
            return preferred_model

        if task_type != "auto" and task_type:
            role = model_registry.get_role_for_agent(task_type)
            return model_registry.resolve_model(role)

        routing = self.rule_based_route(message)
        agent = routing.get("agent", "general") if routing else "general"
        role = model_registry.get_role_for_agent(agent)
        return model_registry.resolve_model(role)

    def classify_task(self, message: str) -> str:
        """Backward-compatible task classification helper."""
        res = self.rule_based_route(message)
        return res.get("intent", "general") if res else "general"

    def get_all_models(self) -> Dict[str, str]:
        """Return dict of role to active effective model."""
        models = {}
        for role in ["general", "router", "planner", "document", "coding", "risk", "compliance", "safety", "maintenance", "reporting", "critic", "vision", "embedding"]:
            models[role] = model_registry.resolve_model(role)
        return models

    def get_roles(self) -> Dict[str, str]:
        """Return dict of primary roles."""
        return self.get_all_models()

    def set_role(self, role: str, model_name: str):
        """Update active model assignment for role."""
        model_registry.set_role_model(role, model_name)


# Global singleton router
model_router = ModelRouter()
