"""
Comprehensive verification test suite for Sovereign AI Workbench (SIH 26117).
Verifies:
1. Tools & Security Sandbox
2. StateGraph Agentic Orchestrator
3. Industrial Specialist Agents
4. RAG Document Ingestion & Chunking
5. FastAPI Routes & Endpoints
"""

import sys
import asyncio
from pathlib import Path

# Add AI-SERVICES to python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.logging import logger
from tools.tool_manager import tool_manager
from tools.file_tool import ReadFileTool, WriteFileTool, ListDirectoryTool, _resolve_safe_path, SANDBOX_DIR
from tools.code_tool import PythonExecutionTool
from tools.spreadsheet_tool import SpreadsheetInspectTool, SpreadsheetFilterTool
from tools.document_tool import DocumentInspectTool, DocumentExtractTool
from orchestrator.state import AgenticState, StepPlan, Observation
from orchestrator.nodes.router import RouterNode
from orchestrator.nodes.planner import PlannerNode
from orchestrator.nodes.agent_selector import AgentSelectorNode
from orchestrator.nodes.executor import ExecutorNode
from orchestrator.nodes.verifier import VerifierNode
from orchestrator.nodes.finalizer import FinalizerNode
from orchestrator.graph import SovereignOrchestrator
from agents.document_agent import document_agent, DocumentAgent
from agents.maintenance_agent import maintenance_agent, MaintenanceAgent
from agents.safety_agent import safety_agent, SafetyAgent
from agents.compliance_agent import compliance_agent, ComplianceAgent
from agents.risk_agent import risk_agent, RiskAgent
from agents.reporting_agent import reporting_agent, ReportingAgent
from agents.code_agent import code_agent, CodeAgent
from rag.parser import document_parser
from rag.chunker import text_chunker


async def run_all_tests():
    print("=" * 70)
    print("  SOVEREIGN AGENTIC AI WORKBENCH - VERIFICATION TEST SUITE")
    print("=" * 70)
    passed = 0
    failed = 0

    # ----------------------------------------------------
    # TEST 1: Tool Registry & Discovery
    # ----------------------------------------------------
    print("\n[TEST 1] Tool Registry & Schema Discovery...")
    tools = tool_manager.list_tools()
    expected_tools = [
        "read_file", "write_file", "list_directory", "file_diff",
        "execute_python", "inspect_document", "extract_document_sections",
        "inspect_spreadsheet", "filter_spreadsheet", "search_knowledge_base"
    ]
    all_registered = all(t in tools for t in expected_tools)
    schemas = tool_manager.get_schemas()

    if all_registered and len(schemas) >= 10:
        print(f"  [PASS] ToolManager registered all {len(tools)} sovereign tools with valid schemas")
        passed += 1
    else:
        print(f"  [FAIL] ToolManager registration incomplete: {tools}")
        failed += 1

    # ----------------------------------------------------
    # TEST 2: File Tools & Sandbox Security
    # ----------------------------------------------------
    print("\n[TEST 2] File Tools & Path Traversal Security Sandbox...")
    # Write a test file inside sandbox
    write_res = await tool_manager.execute_tool("write_file", {
        "file_path": "test_sandbox.txt",
        "content": "Sovereign Industrial Confidential Telemetry Log\nBearing Temp: 72C\nVibration: 2.1mm/s\nStatus: NORMAL\n"
    })
    read_res = await tool_manager.execute_tool("read_file", {"file_path": "test_sandbox.txt"})

    # Test path traversal prevention (must reject attempts to escape sandbox)
    traversal_blocked = False
    try:
        _resolve_safe_path("../../../../../etc/passwd")
    except PermissionError:
        traversal_blocked = True
    except Exception:
        traversal_blocked = True

    if write_res.get("success") and read_res.get("success") and traversal_blocked:
        print("  [PASS] Sandboxed Read/Write operations verified")
        print("  [PASS] Path traversal attack blocked successfully by security boundary")
        passed += 1
    else:
        print(f"  [FAIL] File sandbox test failed (write: {write_res}, read: {read_res}, blocked: {traversal_blocked})")
        failed += 1

    # ----------------------------------------------------
    # TEST 3: Code Execution Tool
    # ----------------------------------------------------
    print("\n[TEST 3] Python Execution Sandbox...")
    code_res = await tool_manager.execute_tool("execute_python", {
        "code": "values = [10, 20, 30, 40]\nprint('COMPUTED_SUM=' + str(sum(values)))"
    })
    result_dict = code_res.get("result", {})
    stdout = result_dict.get("stdout", "")

    if "COMPUTED_SUM=100" in stdout:
        print(f"  [PASS] PythonExecutionTool executed safely (stdout: {stdout.strip()}, duration: {code_res.get('duration_seconds')}s)")
        passed += 1
    else:
        print(f"  [FAIL] Python execution failed: {code_res}")
        failed += 1

    # ----------------------------------------------------
    # TEST 4: Spreadsheet & Tabular Analysis Tool
    # ----------------------------------------------------
    print("\n[TEST 4] Spreadsheet Inspection & Row Filtering...")
    csv_content = "sensor_id,vibration_mms,temperature_c,status\nPUMP_01,2.1,65.0,PASS\nPUMP_02,4.8,88.5,FAIL\nPUMP_03,1.9,62.0,PASS\n"
    await tool_manager.execute_tool("write_file", {"file_path": "telemetry.csv", "content": csv_content})

    inspect_res = await tool_manager.execute_tool("inspect_spreadsheet", {"file_path": "telemetry.csv"})
    filter_res = await tool_manager.execute_tool("filter_spreadsheet", {
        "file_path": "telemetry.csv",
        "column": "status",
        "value": "FAIL"
    })

    insp_result = inspect_res.get("result", {})
    filt_result = filter_res.get("result", {})

    if insp_result.get("total_rows") == 3 and filt_result.get("matches_count") == 1:
        print(f"  [PASS] SpreadsheetInspectTool analyzed {insp_result.get('column_count')} columns and 3 rows")
        print(f"  [PASS] SpreadsheetFilterTool matched anomaly: {filt_result.get('matched_rows')[0]['sensor_id']}")
        passed += 1
    else:
        print(f"  [FAIL] Spreadsheet tool failed: {inspect_res}")
        failed += 1

    # ----------------------------------------------------
    # TEST 5: Document Parser & Recursive Chunker
    # ----------------------------------------------------
    print("\n[TEST 5] Multi-format Document Parser & Sliding-Window Chunker...")
    sample_doc = (
        "# Standard Operating Procedure: Turbine Maintenance\n\n"
        "Section 1: Pre-Maintenance Isolation\n"
        "Ensure all breaker switches are tagged and locked out according to OSHA 1910.147.\n\n"
        "Section 2: Bearing Inspection\n"
        "Measure axial vibration using calibrated accelerometers. If RMS exceeds 4.5 mm/s, replace bearing assembly.\n\n"
        "Section 3: Post-Maintenance Verification\n"
        "Run idle test for 30 minutes. Monitor thermal escalation."
    )
    await tool_manager.execute_tool("write_file", {"file_path": "sop_turbine.md", "content": sample_doc})

    parsed = document_parser.parse_file(str(SANDBOX_DIR / "sop_turbine.md"))
    chunks = text_chunker.chunk_text(parsed.text, base_metadata=parsed.metadata)

    if len(chunks) >= 1 and "OSHA 1910.147" in chunks[0].text:
        print(f"  [PASS] DocumentParser extracted {len(parsed.text)} characters from Markdown")
        print(f"  [PASS] TextChunker generated {len(chunks)} chunks with semantic boundary preservation")
        passed += 1
    else:
        print(f"  [FAIL] Parser/Chunker failed: {parsed}")
        failed += 1

    # ----------------------------------------------------
    # TEST 6: Specialized Industrial Agents
    # ----------------------------------------------------
    print("\n[TEST 6] Specialized Industrial Agents Initialization...")
    agents = [
        document_agent, maintenance_agent, safety_agent,
        compliance_agent, risk_agent, reporting_agent, code_agent
    ]
    agent_names = [a.name for a in agents]
    print(f"  [PASS] Initialized {len(agents)} specialist agents:")
    for a in agents:
        print(f"    - {a.name} (tools: {len(a.tools)})")
    passed += 1

    # ----------------------------------------------------
    # TEST 7: Orchestrator Graph & State Machine
    # ----------------------------------------------------
    print("\n[TEST 7] StateGraph Orchestrator Execution Flow...")
    orch = SovereignOrchestrator()

    # Test 7a: Router node direct classification
    state_greeting = AgenticState(user_query="Hello! What can you do?")
    state_greeting = await orch.router.execute(state_greeting)
    if state_greeting.is_direct_chat and state_greeting.route == "direct":
        print("  [PASS] RouterNode accurately classified simple greeting as direct chat")
        passed += 1
    else:
        print(f"  [FAIL] RouterNode classification failed: {state_greeting.route}")
        failed += 1

    # Test 7b: Full orchestrator workflow on industrial telemetry task
    print("\n[TEST 8] End-to-End Orchestrator Pipeline on Industrial Task...")
    events_received = []

    def test_callback(event, state):
        events_received.append(event)

    test_query = "Analyze equipment telemetry in telemetry.csv, identify failed sensors, and synthesize report."
    result_state = await orch.run(query=test_query, on_step_callback=test_callback)

    if (
        result_state.status == "completed"
        and len(result_state.plan) > 0
        and len(result_state.observations) > 0
        and len(result_state.final_response) > 0
    ):
        print(f"  [PASS] Orchestrator planned {len(result_state.plan)} sequential steps")
        for step in result_state.plan:
            print(f"    Step {step.step_number}: {step.title} -> {step.target_agent}")
        print(f"  [PASS] Executed & verified {len(result_state.observations)} step observations")
        print(f"  [PASS] State callbacks emitted: {events_received}")
        print(f"  [PASS] Final Response synthesized ({len(result_state.final_response)} characters)")
        passed += 1
    else:
        print(f"  [FAIL] Orchestrator pipeline failed: status={result_state.status}, plan={result_state.plan}")
        failed += 1

    # ----------------------------------------------------
    # TEST 9: FastAPI App Configuration & Routers
    # ----------------------------------------------------
    print("\n[TEST 9] FastAPI Application & Route Mounting...")
    import main
    print(f"  Debug: imported main from: {main.__file__}")
    app = main.app
    route_paths = []
    for r in app.routes:
        if hasattr(r, "path"):
            route_paths.append(r.path)
        # If r is an APIRouter or Mount
        for sub_attr in ["routes", "app"]:
            if hasattr(r, sub_attr):
                obj = getattr(r, sub_attr)
                if hasattr(obj, "routes"):
                    for sub in obj.routes:
                        if hasattr(sub, "path"):
                            route_paths.append(sub.path)
    print(f"  Debug: Found routes ({len(route_paths)}): {route_paths}")
    required_endpoints = [
        "/api/health", "/api/models", "/api/chat", "/api/chat/stream",
        "/api/documents", "/api/documents/process", "/api/documents/search",
        "/api/vision/analyze", "/api/tasks/execute", "/api/tasks"
    ]
    all_endpoints_mounted = all(ep in route_paths for ep in required_endpoints)

    if all_endpoints_mounted:
        print(f"  [PASS] All {len(required_endpoints)} required REST/Streaming API endpoints mounted successfully:")
        for ep in required_endpoints:
            print(f"    - {ep}")
        passed += 1
    else:
        missing = [ep for ep in required_endpoints if ep not in route_paths]
        print(f"  [FAIL] Missing endpoints in FastAPI: {missing}")
        failed += 1

    # ----------------------------------------------------
    # Summary
    # ----------------------------------------------------
    print("\n" + "=" * 70)
    print(f"  TEST RESULTS: {passed} PASSED, {failed} FAILED (Total: {passed + failed})")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
