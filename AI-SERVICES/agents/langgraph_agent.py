"""
Sovereign LangGraph Autonomous Agent Engine.
Executes specialized and general agents through a compiled LangGraph StateGraph.
Supports dynamic tool binding, multi-turn reasoning loops:
START -> agent -> should_continue -> (tools -> agent) OR (END)
"""

import os
import re
import json
import uuid
import asyncio
from pathlib import Path
from typing import TypedDict, Annotated, List, Dict, Any, Optional, AsyncGenerator

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama

from tools.agent_tools import get_agent_tools, resolve_tool, TOOLS_MAP, SANDBOX_DIR
from core.config import settings
from core.logging import logger


class AgentState(TypedDict):
    """Sovereign Agent LangGraph State schema."""
    messages: Annotated[List[BaseMessage], add_messages]
    task: Optional[str]
    selected_model: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    tool_executions: List[Dict[str, Any]]
    generated_files: List[Dict[str, Any]]
    errors: List[str]


DEFAULT_SYSTEM_PROMPT = (
    "You are the Sovereign On-Premise AI Agent Workbench assistant.\n"
    "You operate strictly within a secure, on-premise, air-gapped infrastructure with verified local tools.\n\n"
    "AVAILABLE SOVEREIGN TOOLS:\n"
    "- `execute_python` (arguments: `code`: str): Executes Python code in an isolated sandbox. Returns stdout, stderr, exit_code.\n"
    "- `create_file` (arguments: `file_path`: str, `content`: str): Creates or updates a file in the workspace.\n"
    "- `read_file` (arguments: `file_path`: str): Reads file contents inside the workspace.\n"
    "- `list_files` (arguments: `dir_path`: str): Lists files and directories in the workspace.\n"
    "- `create_directory` (arguments: `dir_path`: str): Creates a directory in the workspace.\n"
    "- `create_pdf` (arguments: `file_name`: str, `title`: str, `content`: str): Compiles a real PDF using ReportLab in reports/.\n\n"
    "TOOL EXECUTION INSTRUCTIONS:\n"
    "To use a tool, you MUST output a JSON object in the following format ON A NEW LINE by itself:\n"
    "```json\n"
    "{\n"
    "  \"name\": \"<tool_name>\",\n"
    "  \"arguments\": {\n"
    "    \"<arg1>\": \"<val1>\"\n"
    "  }\n"
    "}\n"
    "```\n"
    "You may ONLY call one tool at a time.\n"
    "Wait for the observation before continuing your response.\n\n"
    "RESPONSE & CODING GUIDELINES:\n"
    "1. When asked to write, give, or explain code (Python, C++, Java, JavaScript, etc.):\n"
    "   - ALWAYS provide complete, fully functional, production-quality code.\n"
    "   - ALWAYS enclose code inside standard markdown fenced blocks specifying the language identifier.\n"
    "   - If the user asks you to run, execute, or calculate using Python, YOU MUST CALL THE `execute_python` TOOL using the JSON format above.\n"
    "2. When a tool is executed, review the observation and synthesize a final response.\n"
    "3. For general conceptual queries, answer directly without invoking tools."
)


def normalize_tool_calls(response: AIMessage) -> AIMessage:
    """
    Ensure tool calls are structured in standard format.
    Handles models that output structured JSON (single or multiple) inside content rather than native tool_calls.
    """
    if hasattr(response, "tool_calls") and response.tool_calls:
        return response

    content = (response.content or "").strip()
    if not content:
        return response

    # Strip markdown code blocks: ```json ... ``` or ``` ... ```
    cleaned = re.sub(r'```(?:json)?\s*', '', content).replace('```', '').strip()

    tool_calls = []

    # First, try line-by-line parsing for models outputting JSON lines
    for line in cleaned.splitlines():
        line_str = line.strip()
        if not line_str or not (line_str.startswith("{") and line_str.endswith("}")):
            continue
        try:
            data = json.loads(line_str)
            if isinstance(data, dict) and ("name" in data or "tool" in data):
                t_name = data.get("name") or data.get("tool")
                t_args = data.get("arguments") or data.get("parameters") or data.get("args") or {}
                if isinstance(t_args, dict):
                    cleaned_args = {}
                    for k, v in t_args.items():
                        cleaned_args[k] = v["value"] if isinstance(v, dict) and "value" in v else v
                    t_args = cleaned_args
                resolved = resolve_tool(t_name)
                if resolved:
                    call_id = f"call_{uuid.uuid4().hex[:8]}"
                    tool_calls.append({"name": resolved.name, "args": t_args, "id": call_id})
                    logger.info(f"[AGENT] Parsed structured tool call: {resolved.name}({t_args})")
        except Exception:
            pass

    # If line-by-line didn't match, search for any JSON objects
    if not tool_calls:
        for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned):
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
                if isinstance(data, dict) and ("name" in data or "tool" in data):
                    t_name = data.get("name") or data.get("tool")
                    t_args = data.get("arguments") or data.get("parameters") or data.get("args") or {}
                    if isinstance(t_args, dict):
                        cleaned_args = {}
                        for k, v in t_args.items():
                            cleaned_args[k] = v["value"] if isinstance(v, dict) and "value" in v else v
                        t_args = cleaned_args
                    resolved = resolve_tool(t_name)
                    if resolved:
                        call_id = f"call_{uuid.uuid4().hex[:8]}"
                        tool_calls.append({"name": resolved.name, "args": t_args, "id": call_id})
                        logger.info(f"[AGENT] Parsed structured tool call: {resolved.name}({t_args})")
            except Exception:
                pass

    if tool_calls:
        return AIMessage(content="", tool_calls=tool_calls)

    return response


class SovereignLangGraphAgent:
    """
    Compiled LangGraph Agent for on-premise execution.
    Handles graph compilation, step execution, and streaming.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ):
        self.model_name = model_name or settings.OLLAMA_CHAT_MODEL
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = get_agent_tools()

        # Build ChatOllama instance
        kwargs = {
            "model": self.model_name,
            "base_url": settings.OLLAMA_BASE_URL,
            "temperature": self.temperature,
            "num_predict": max(self.max_tokens or 4096, 2048),
        }

        self.llm = ChatOllama(**kwargs)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Construct and compile the LangGraph StateGraph."""
        workflow = StateGraph(AgentState)

        # Agent Node
        def agent_node(state: AgentState):
            msgs = state["messages"]
            logger.info(f"[AGENT] Model: {self.model_name} | Messages: {len(msgs)}")
            resp = self.llm_with_tools.invoke(msgs)
            normalized = normalize_tool_calls(resp)

            if getattr(normalized, "tool_calls", None):
                for tc in normalized.tool_calls:
                    logger.info(f"[AGENT] Tool call: {tc['name']} with args: {tc.get('args', {})}")
            else:
                snippet = (normalized.content or "").strip()[:80].replace("\n", " ")
                logger.info(f"[AGENT] Direct response (no tools requested): '{snippet}...'")

            return {"messages": [normalized]}

        # Tool Decision Node
        def should_continue(state: AgentState):
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tools"
            return END

        # Tool Execution Node
        def tool_node(state: AgentState):
            import time
            last = state["messages"][-1]
            tool_calls = getattr(last, "tool_calls", [])
            tool_msgs = []
            recorded_calls = list(state.get("tool_calls", []))
            recorded_results = list(state.get("tool_results", []))
            recorded_executions = list(state.get("tool_executions", []))
            generated_files = list(state.get("generated_files", []))

            for tc in tool_calls:
                t_name = tc["name"]
                t_args = tc.get("args", {})
                cid = tc.get("id", f"call_{uuid.uuid4().hex[:8]}")

                logger.info(f"[AGENT] Executing tool: {t_name}")
                recorded_calls.append({"tool": t_name, "arguments": t_args, "id": cid})

                start_t = time.time()
                tool_fn = resolve_tool(t_name)
                if tool_fn:
                    try:
                        result_str = tool_fn.invoke(t_args)
                        duration = round(time.time() - start_t, 3)
                        try:
                            res_obj = json.loads(result_str)
                        except Exception:
                            res_obj = {"raw": result_str}

                        status_str = "success" if res_obj.get("success", True) else "failed"
                        logger.info(f"[AGENT] Tool result: {t_name} -> {status_str} ({duration}s)")

                        # Check for file generation
                        if (
                            t_name in ["create_pdf", "create_file", "pdf.create", "file.create"]
                            and isinstance(res_obj, dict)
                            and res_obj.get("success")
                        ):
                            fname = res_obj.get("file_name") or Path(res_obj.get("file_path", "")).name
                            file_info = {
                                "name": fname,
                                "path": res_obj.get("file_path"),
                                "mime_type": res_obj.get("mime_type", "text/plain"),
                                "size_bytes": res_obj.get("size_bytes", 0)
                            }
                            generated_files.append(file_info)
                            logger.info(f"[AGENT] File generated: {fname} ({res_obj.get('file_path')})")

                        execution_record = {
                            "tool": t_name,
                            "arguments": t_args,
                            "result": res_obj,
                            "id": cid,
                            "duration_seconds": duration,
                            "success": res_obj.get("success", True) if isinstance(res_obj, dict) else True,
                            "stdout": res_obj.get("stdout", "") if isinstance(res_obj, dict) else "",
                            "stderr": res_obj.get("stderr", "") if isinstance(res_obj, dict) else "",
                            "exit_code": res_obj.get("exit_code", 0) if isinstance(res_obj, dict) else 0,
                            "timestamp": time.time()
                        }
                        recorded_executions.append(execution_record)

                    except Exception as e:
                        duration = round(time.time() - start_t, 3)
                        logger.error(f"[AGENT] Tool execution exception in {t_name}: {e}")
                        result_str = json.dumps({"success": False, "error": str(e)})
                        res_obj = {"success": False, "error": str(e)}
                        recorded_executions.append({
                            "tool": t_name,
                            "arguments": t_args,
                            "result": res_obj,
                            "id": cid,
                            "duration_seconds": duration,
                            "success": False,
                            "stderr": str(e),
                            "exit_code": 1
                        })
                else:
                    err = f"Tool '{t_name}' not found in sovereign registry."
                    logger.error(f"[AGENT] {err}")
                    result_str = json.dumps({"success": False, "error": err})
                    res_obj = {"success": False, "error": err}
                    recorded_executions.append({
                        "tool": t_name,
                        "arguments": t_args,
                        "result": res_obj,
                        "id": cid,
                        "duration_seconds": 0.0,
                        "success": False,
                        "stderr": err,
                        "exit_code": 1
                    })

                recorded_results.append({"tool": t_name, "result": res_obj, "id": cid})
                tool_msgs.append(ToolMessage(content=result_str, tool_call_id=cid))

            logger.info("[AGENT] Returning tool result to LLM")
            return {
                "messages": tool_msgs,
                "tool_calls": recorded_calls,
                "tool_results": recorded_results,
                "tool_executions": recorded_executions,
                "generated_files": generated_files,
            }

        # Add nodes and edges
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    async def execute(self, query: str) -> Dict[str, Any]:
        """Run non-streaming workflow execution."""
        logger.info(f"[AGENT] Starting agent execution for query: {query[:60]}...")
        init_state: AgentState = {
            "messages": [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=query)
            ],
            "task": query,
            "selected_model": self.model_name,
            "tool_calls": [],
            "tool_results": [],
            "tool_executions": [],
            "generated_files": [],
            "errors": []
        }

        # Run in thread pool to avoid blocking async loop
        final_state = await asyncio.to_thread(self.graph.invoke, init_state)
        last_message = final_state["messages"][-1]
        final_text = getattr(last_message, "content", "")

        logger.info(f"[AGENT] Completed task. Tool calls: {len(final_state.get('tool_calls', []))}")
        return {
            "final_response": final_text,
            "selected_model": self.model_name,
            "tool_calls": final_state.get("tool_calls", []),
            "tool_results": final_state.get("tool_results", []),
            "tool_executions": final_state.get("tool_executions", []),
            "generated_files": final_state.get("generated_files", []),
            "messages": final_state.get("messages", []),
        }

    async def stream(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream workflow execution emitting granular real-time events:
        - agent:start
        - agent:model
        - agent:tool:start
        - agent:tool:result (with stdout, execution time, exit_code)
        - agent:file:created
        - token / content chunks
        - completed (with generatedFiles and toolExecutions)
        """
        logger.info(f"[AGENT] Starting streaming agent execution: {query[:60]}...")

        # 1. Emit start event
        yield {
            "event": "agent:start",
            "agent": "general",
            "model": self.model_name,
            "status": "started"
        }

        yield {
            "event": "agent:model",
            "model": self.model_name
        }

        # Execute full LangGraph flow with periodic keepalive
        exec_task = asyncio.create_task(self.execute(query))
        while not exec_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(exec_task), timeout=3.0)
            except asyncio.TimeoutError:
                yield {
                    "event": "agent:thinking",
                    "status": "processing"
                }

        result = await exec_task

        # 2. Emit all tool events that occurred
        for te in result.get("tool_executions", []):
            yield {
                "event": "agent:tool:start",
                "tool": te["tool"],
                "status": "started",
                "arguments": te.get("arguments", {})
            }
            yield {
                "event": "agent:tool:result",
                "tool": te["tool"],
                "status": "completed",
                "result": te.get("result", {}),
                "arguments": te.get("arguments", {}),
                "duration_seconds": te.get("duration_seconds", 0),
                "stdout": te.get("stdout", ""),
                "stderr": te.get("stderr", ""),
                "exit_code": te.get("exit_code", 0),
                "success": te.get("success", True)
            }

        # 3. Emit file created events
        for gf in result.get("generated_files", []):
            yield {
                "event": "agent:file:created",
                "file": gf
            }

        # 4. Stream response tokens in progressive micro-chunks
        final_text = result.get("final_response", "")
        logger.info(f"[AGENT] Generating micro-chunks for final_text (len={len(final_text)}): {final_text[:60]}")
        chunk_size = 18
        for i in range(0, len(final_text), chunk_size):
            chunk = final_text[i:i + chunk_size]
            yield {
                "token": chunk,
                "content": chunk
            }
            await asyncio.sleep(0.012)

        # 5. Emit completed event
        yield {
            "status": "completed",
            "final_response": final_text,
            "generatedFiles": result.get("generated_files", []),
            "tool_calls": result.get("tool_calls", []),
            "tool_executions": result.get("tool_executions", []),
        }
        logger.info(f"[AGENT] Streaming completed for agent.")


from llm.model_registry import model_registry

# Helper factory functions
def get_langgraph_agent(
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> SovereignLangGraphAgent:
    """Create a configured SovereignLangGraphAgent instance with tool support."""
    eff_model = model_registry.get_agent_model(model)

    return SovereignLangGraphAgent(
        model_name=eff_model,
        system_prompt=system_prompt,
        temperature=temperature if temperature is not None else 0.1,
        max_tokens=max_tokens
    )
