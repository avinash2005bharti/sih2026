from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from llm.ollama_client import ollama_client
from core.config import settings

class GeneralAssistant(BaseAgent):
    agent_id: str = "general_assistant"
    name: str = "general_assistant"
    display_name: str = "General Assistant"
    description: str = "General sovereign industrial assistant for queries, explanations, and lightweight task support."
    system_prompt: str = (
        "You are the Sovereign General Assistant for an on-premise industrial AI workbench. "
        "You operate in a confidential, air-gapped environment. Provide accurate, professional, "
        "and concise assistance for engineering and manufacturing queries. If a task requires multi-step "
        "planning, code generation, or formal report generation, coordinate with specialized agents."
    )
    capabilities: List[str] = ["general_qa", "technical_explanation", "conversational"]
    allowed_tools: List[str] = ["rag_search", "file_reader"]
    preferred_model: str = settings.DEFAULT_GENERAL_MODEL

    async def process(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if conversation_history:
            for h in conversation_history[-6:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        res = await ollama_client.chat(messages=messages, model=self.preferred_model)
        return {
            "agent_id": self.agent_id,
            "agent_name": self.display_name,
            "content": res.get("content", ""),
            "model_used": res.get("model", self.preferred_model)
        }

general_assistant = GeneralAssistant()
