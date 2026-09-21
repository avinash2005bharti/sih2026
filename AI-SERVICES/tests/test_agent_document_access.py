"""
Verification test suite for Agent Document Section Access
Tests that all agents, tools, registries, and context builders have unrestricted
access to the document section, database documents, and file content.
"""
import asyncio
import os
import sys

# Ensure AI-SERVICES is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_registry import central_tool_registry
from tools.tool_manager import ToolManager
from agents.agent_registry import AGENT_REGISTRY
from orchestrator.task_classifier import AGENT_PROMPTS
from orchestrator.nodes.planner import build_planner_prompt
from memory.context_builder import central_context_builder


async def test_tool_registry_document_tools():
    print("=== Testing Tool Registry Document Tools ===")
    required_tools = [
        "list_documents",
        "get_document",
        "get_document_content",
        "search_database_documents",
        "create_document",
        "update_document",
        "delete_document",
    ]
    for tool_name in required_tools:
        tool = central_tool_registry.get_tool(tool_name)
        assert tool is not None, f"Tool '{tool_name}' must be registered in central_tool_registry!"
        print(f"  [OK] Found tool: {tool_name} -> {tool.name}")
    print("[PASS] CentralToolRegistry document tools verified.\n")


async def test_tool_execution():
    print("=== Testing ToolManager Execution ===")
    tm = ToolManager()
    
    # 1. list_documents
    list_res = await tm.execute_tool("list_documents", {"limit": 10})
    print(f"  list_documents success: {list_res.get('success')}, count: {list_res.get('total')}")
    assert list_res.get("success") is True, f"list_documents failed: {list_res}"
    docs = list_res.get("documents", [])
    assert len(docs) > 0, "Expected at least 1 document in database/workspace"
    sample_doc = docs[0]
    sample_name = sample_doc.get("name") or sample_doc.get("originalName")
    print(f"  Sample doc name: '{sample_name}', ID: {sample_doc.get('document_id')}")

    # 2. get_document
    get_res = await tm.execute_tool("get_document", {"name_or_id": sample_name})
    print(f"  get_document success: {get_res.get('success')}")
    assert get_res.get("success") is True, f"get_document failed: {get_res}"

    # 3. get_document_content
    content_res = await tm.execute_tool("get_document_content", {"file_name_or_id": sample_name})
    print(f"  get_document_content success: {content_res.get('success')}, text length: {len(content_res.get('text', ''))}")
    assert content_res.get("success") is True, f"get_document_content failed: {content_res}"

    # 4. search_database_documents
    search_res = await tm.execute_tool("search_database_documents", {"query": "AI", "limit": 5})
    print(f"  search_database_documents success: {search_res.get('success')}, matches: {search_res.get('total')}")
    assert search_res.get("success") is True, f"search_database_documents failed: {search_res}"

    print("[PASS] ToolManager execution verified.\n")


async def test_agent_registry():
    print("=== Testing AGENT_REGISTRY Document Access ===")
    doc_tools = {"list_documents", "get_document", "get_document_content", "search_database_documents"}
    for agent_id, agent_cfg in AGENT_REGISTRY.items():
        tools = set(agent_cfg.get("available_tools", []))
        missing = doc_tools - tools
        assert not missing, f"Agent '{agent_id}' is missing tools: {missing}"
        assert agent_cfg.get("rag_enabled") is True, f"Agent '{agent_id}' must have rag_enabled: True"
        prompt = agent_cfg.get("system_prompt", "")
        assert "DOCUMENT SECTION & REPOSITORY ACCESS" in prompt, f"Agent '{agent_id}' prompt missing document access section"
        print(f"  [OK] Agent '{agent_id}': tools={len(tools)}, rag_enabled=True, prompt=verified")
    print("[PASS] All AGENT_REGISTRY agents have full document access.\n")


async def test_task_classifier_prompts():
    print("=== Testing AGENT_PROMPTS Document Access ===")
    for agent_id, prompt in AGENT_PROMPTS.items():
        assert "DOCUMENT SECTION ACCESS" in prompt, f"Prompt for '{agent_id}' missing DOCUMENT SECTION ACCESS"
        assert "list_documents" in prompt, f"Prompt for '{agent_id}' missing list_documents tool reference"
        print(f"  [OK] Task classifier prompt for '{agent_id}' verified.")
    print("[PASS] Task classifier prompts verified.\n")


async def test_context_builder():
    print("=== Testing ContextBuilder Document Section Injection ===")
    enriched = await central_context_builder.build(
        conversation_id="test_conv",
        user_id="test_user",
        is_admin=False,  # Even non-admin agents must get access to all documents
        query="What documents are in my document section and what do they contain?",
        agent_id="general"
    )
    sys_prompt = enriched.system_prompt
    assert "Workspace Document Repository (Document Section)" in sys_prompt or "Available Database & Workspace Documents" in sys_prompt, "ContextBuilder did not inject document section summary into system prompt!"
    assert "list_documents" in sys_prompt or "get_document_content" in sys_prompt, "Document tool directives missing from enriched system prompt!"
    print(f"  [OK] Enriched prompt contains Document Section context (length: {len(sys_prompt)} chars)")
    print("[PASS] ContextBuilder document injection verified.\n")


async def main():
    print("Starting Comprehensive Agent Document Access Tests...\n")
    await test_tool_registry_document_tools()
    await test_tool_execution()
    await test_agent_registry()
    await test_task_classifier_prompts()
    await test_context_builder()
    print("ALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())
