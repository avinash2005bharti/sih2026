import os
import sys
import json
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
AI_SERVICES_DIR = CURRENT_DIR.parent
PROJECT_ROOT = AI_SERVICES_DIR.parent
sys.path.insert(0, str(AI_SERVICES_DIR))

from orchestrator.task_classifier import task_classifier
from agents.langgraph_agent import SovereignLangGraphAgent, normalize_tool_calls
from langchain_core.messages import AIMessage


def test_agent_integration():
    print("=== TESTING AGENT TASK ROUTING & TOOL INTEGRATION ===")

    # 1. Test Task Classification for terminal command
    c1 = task_classifier.classify("Run a terminal command to check directory contents")
    print(f"Classification 1 ('Run terminal command'): agent={c1.agent}, task_type={c1.task_type}, requires_tools={c1.requires_tools}")
    assert c1.agent == "code_agent"
    assert c1.requires_tools is True

    # 2. Test Task Classification for document analysis and deliverable creation
    c2 = task_classifier.classify("Analyze the uploaded document 1789822346748-589300_20250423-EB-Event-Driven_Design_for_Agents.PDF and create a new file based on it")
    print(f"Classification 2 ('Analyze document & create new file'): agent={c2.agent}, task_type={c2.task_type}, requires_tools={c2.requires_tools}")
    assert c2.agent == "document_agent"
    assert c2.requires_tools is True

    # 3. Test Tool Calling Normalization for file_terminal_operations
    test_msg = AIMessage(
        content='''{"name": "file_terminal_operations", "arguments": {"action": "terminal", "command": "python --version"}}'''
    )
    norm = normalize_tool_calls(test_msg)
    print(f"Normalized tool calls: {norm.tool_calls}")
    assert len(norm.tool_calls) == 1
    assert norm.tool_calls[0]["name"] == "file_terminal_operations"
    assert norm.tool_calls[0]["args"]["action"] == "terminal"

    # 4. Test Tool Calling Normalization with alias
    test_msg_alias = AIMessage(
        content='''{"name": "file_terminal", "arguments": {"action": "read", "target": "1789822346748-589300_20250423-EB-Event-Driven_Design_for_Agents.PDF"}}'''
    )
    norm_alias = normalize_tool_calls(test_msg_alias)
    print(f"Normalized alias tool calls: {norm_alias.tool_calls}")
    assert len(norm_alias.tool_calls) == 1
    assert norm_alias.tool_calls[0]["name"] == "file_terminal_operations"

    print("ALL AGENT ROUTING AND NORMALIZATION TESTS PASSED!")


if __name__ == "__main__":
    test_agent_integration()
