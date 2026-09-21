import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routes.chat import ChatRequest, chat_stream
from memory.context_builder import central_context_builder
from orchestrator.task_classifier import task_classifier
from llm.model_router import model_router
from agents.langgraph_agent import get_langgraph_agent

async def main():
    query = "can tell me how many document i have in my document sections"
    print("=== 1. CLASSIFICATION ===")
    routing = task_classifier.classify(query, has_images=False)
    print("Task type:", routing.task_type)
    print("Agent:", routing.agent)

    print("\n=== 2. MODEL ROUTER ===")
    model = model_router.route(query, task_type=routing.task_type)
    print("Resolved model:", model)

    print("\n=== 3. CONTEXT BUILDER ===")
    enriched = await central_context_builder.build(
        conversation_id="test_direct_debug",
        query=query,
        agent_id=routing.agent
    )
    print("Intent:", enriched.intent)
    print("System prompt chars:", len(enriched.system_prompt))
    print("Doc repo count:", enriched.observability.get("repo_documents_count"))
    print("RAG chunks count:", enriched.observability.get("rag_chunks_count"))

    print("\n=== 4. RUN AGENT EXECUTE (ONE-SHOT) ===")
    agent = get_langgraph_agent(
        model=model,
        system_prompt=enriched.system_prompt
    )
    print("Agent initialized with model:", agent.model_name)
    print("Executing query...")
    result = await agent.execute(query=query, conversation_id="test_direct_debug")
    print("\n=== FINAL AGENT RESPONSE ===")
    print(result.get("final_response"))
    print("Tool calls made:", len(result.get("tool_calls", [])))

if __name__ == "__main__":
    asyncio.run(main())
