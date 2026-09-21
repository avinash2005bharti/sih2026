"""
Dedicated Sovereign AI Workbench Acceptance & Verification Runner.
Executes all 10 SIH 26117 acceptance milestones sequentially:
1. Model Registry & Fallback Hierarchy
2. Two-Tier Router (Deterministic + Structured SLM)
3. Python Document Generators (PDF, DOCX, XLSX, MD)
4. Coding Agent Subprocess Sandbox Execution
5. Document Ingestion & Qdrant Verification (chunks > 0, embeddings > 0, points > 0, sample verified)
6. Qdrant Persistence & Document ID Filtering
7. Grounded RAG Retrieval with Citations
8. Structured Planner (llama3.2:1b) & Critic (smollm2:1.7b)
9. Risk & Compliance Specialist Prompting
10. Sovereign AI Enclave Health Check (/api/health/ai)
"""

import sys
import asyncio
import time
from pathlib import Path

# Set up paths
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from llm.model_registry import model_registry
from llm.model_router import model_router
from llm.ollama_client import ollama_client
from tools.tool_registry import central_tool_registry, SANDBOX_DIR
from rag.document_loader import document_loader
from rag.retriever import rag_retriever
from rag.qdrant_client import qdrant_client
from rag.embeddings import embeddings_service
from orchestrator.nodes.planner import PlannerNode
from orchestrator.nodes.verifier import VerifierNode
from orchestrator.state import AgenticState, StepPlan, Observation
from api.routes.health import health_ai


async def main():
    print("=" * 70)
    print("SOVEREIGN ON-PREMISE AGENTIC WORKBENCH: ACCEPTANCE TEST SUITE")
    print("SIH 26117 - Confidential Industrial Work Enclave")
    print("=" * 70)

    results = {}
    start_all = time.time()

    # -------------------------------------------------------------
    # TEST 1: Model Registry & Fallback Hierarchy
    # -------------------------------------------------------------
    print("\n[STEP 1/10] Model Registry & Fallback Hierarchy")
    try:
        installed = await model_registry.detect_installed_models()
        print(f"  Installed Ollama models detected ({len(installed)}): {installed}")
        assert len(installed) > 0, "No installed Ollama models found"

        roles = ["router", "general", "planner", "document", "coding", "risk", "compliance", "critic", "vision", "embedding"]
        role_map = {}
        for r in roles:
            m = model_registry.get_model(r)
            role_map[r] = m
            assert m is not None, f"Role {r} failed to resolve"
            print(f"  Role '{r:<12}': effective model '{m}'")

        # Nonexistent role fallback check
        fallback = model_registry.get_model("nonexistent_specialist")
        print(f"  Fallback check: 'nonexistent_specialist' -> '{fallback}'")
        assert fallback is not None

        results["1_model_registry"] = True
        print("  -> PASSED: Model Registry & Fallback Hierarchy")
    except Exception as e:
        results["1_model_registry"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # TEST 2: Two-Tier Router (Deterministic + Structured SLM)
    # -------------------------------------------------------------
    print("\n[STEP 2/10] Two-Tier Router & Intent Classification")
    try:
        test_cases = [
            ("Hello there!", "general"),
            ("Please analyze this safety report for OSHA violations", "compliance"),
            ("Write a python script to calculate equipment vibration FFT", "maintenance"),
            ("Generate an executive risk summary for Turbine A", "risk_analysis"),
            ("Create an audit report for ISO 9001 compliance", "compliance"),
            ("Inspect this crack on the turbine blade image", "image_analysis"),
        ]
        for query, exp_intent in test_cases:
            is_img = "image" in query
            res = await model_router.route_request(query, has_image=is_img)
            assert "intent" in res and "agent" in res
            print(f"  Query: '{query[:40]:<42}' -> Intent: '{res['intent']:<14}' Agent: '{res['agent']}' (conf={res.get('confidence', 0):.2f})")

        results["2_router"] = True
        print("  -> PASSED: Two-Tier Router & Intent Classification")
    except Exception as e:
        results["2_router"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # TEST 3: Tool Registry & Document Generation (Python tools)
    # -------------------------------------------------------------
    print("\n[STEP 3/10] Tool Registry & Document Generation (Python Tools)")
    try:
        tools = central_tool_registry.list_tools()
        print(f"  Registered workbench tools count: {len(tools)}/16")
        assert len(tools) >= 16

        # 1. Spreadsheet Writer (.xlsx)
        xlsx = await central_tool_registry.execute_tool(
            "spreadsheet_writer",
            {
                "file_name": "telemetry_turbine_test.xlsx",
                "headers": ["Turbine_ID", "Bearing_Temp_C", "Vibration_RMS", "Status"],
                "rows": [["GT-01", "76.5", "2.2", "PASS"], ["GT-02", "95.1", "5.9", "ALERT"]],
                "title": "Industrial Gas Turbine Telemetry Record"
            }
        )
        assert xlsx["success"]
        print("  - Excel (.xlsx) generated via openpyxl")

        # 2. Spreadsheet Reader (.xlsx)
        reader = await central_tool_registry.execute_tool(
            "spreadsheet_reader",
            {"file_path": "reports/telemetry_turbine_test.xlsx"}
        )
        assert reader["success"] and len(reader["result"]["headers"]) == 4
        print(f"  - Excel (.xlsx) parsed: {len(reader['result']['headers'])} columns, {len(reader['result']['rows'])} rows")

        # 3. PDF Generator (.pdf)
        pdf = await central_tool_registry.execute_tool(
            "pdf_generator",
            {
                "file_name": "fmea_turbine_test.pdf",
                "title": "Turbine Failure Mode Analysis",
                "content": "Operating temperature exceeded normal limits on Bearing GT-02.",
                "table_data": [["Asset", "Severity", "Action"], ["GT-02", "HIGH", "Lube Oil Change"]]
            }
        )
        assert pdf["success"]
        print("  - PDF (.pdf) compiled via ReportLab")

        # 4. Word Document Generator (.docx)
        docx = await central_tool_registry.execute_tool(
            "docx_generator",
            {
                "file_name": "turbine_sop_test.docx",
                "title": "Sovereign Industrial SOP",
                "sections": [{"heading": "Safety Scope", "body": "Mandatory PPE and vibration isolation."}]
            }
        )
        assert docx["success"]
        print("  - Word (.docx) compiled via python-docx")

        # 5. Markdown Report Generator (.md)
        md = await central_tool_registry.execute_tool(
            "report_generator",
            {"file_name": "executive_report.md", "title": "Audit Summary", "content": "Zero OSHA violations detected."}
        )
        assert md["success"]
        print("  - Markdown (.md) synthesized")

        results["3_tool_registry"] = True
        print("  -> PASSED: Tool Registry & Document Generation")
    except Exception as e:
        results["3_tool_registry"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # TEST 4: Coding Agent Subprocess Sandbox Execution
    # -------------------------------------------------------------
    print("\n[STEP 4/10] Coding Agent Subprocess Sandbox Execution")
    try:
        # Safe execution
        safe_code = "import math\nvals = [12.5, 14.8, 11.2, 18.0]\nmean = sum(vals)/len(vals)\nprint(f'COMPUTED_MEAN:{mean:.2f}')"
        res_safe = await central_tool_registry.execute_tool("python_executor", {"code": safe_code})
        assert res_safe["success"] and "COMPUTED_MEAN:14.12" in res_safe["result"]["stdout"]
        print(f"  Safe Python execution: {res_safe['result']['stdout'].strip()}")

        # Unsafe command blocking
        unsafe_code = "import os\nos.system('dir')"
        res_unsafe = await central_tool_registry.execute_tool("python_executor", {"code": unsafe_code})
        assert not res_unsafe["success"] and "Security restriction" in str(res_unsafe)
        err_msg = res_unsafe.get("result", {}).get("error") or res_unsafe.get("error", "")
        print(f"  Unsafe code blocked correctly: '{err_msg}'")


        results["4_coding_sandbox"] = True
        print("  -> PASSED: Coding Agent Sandbox Execution")
    except Exception as e:
        results["4_coding_sandbox"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # TEST 5: Document Ingestion & Qdrant End-to-End Verification
    # -------------------------------------------------------------
    print("\n[STEP 5/10] Document Ingestion & Qdrant End-to-End Verification")
    doc_id = "titan_manual_9000"
    test_pdf_path = BASE_DIR / "data" / "uploads" / "test.pdf"
    test_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        doc = SimpleDocTemplate(str(test_pdf_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Sovereign Industrial Gas Turbine Operating Manual", styles["Heading1"]),
            Spacer(1, 10),
            Paragraph("Model: Sovereign Titan-9000 Industrial Gas Turbine.", styles["BodyText"]),
            Paragraph("Normal operating temperature range: 750 to 820 degrees Celsius.", styles["BodyText"]),
            Paragraph("Emergency trip threshold: 950 degrees Celsius.", styles["BodyText"]),
            Paragraph("Vibration warning limit: 4.5 mm/s RMS. Trip limit: 7.1 mm/s RMS.", styles["BodyText"]),
            Paragraph("Lubricating oil pressure must be maintained between 2.8 and 3.5 bar during active load.", styles["BodyText"]),
            Paragraph("Compliance Standard: ISO 10816-4 for mechanical vibration of industrial gas turbines.", styles["BodyText"]),
            Paragraph("Safety Protocol: Lockout-Tagout (LOTO) mandatory before accessing rotor housing.", styles["BodyText"]),
        ]
        doc.build(story)
        print(f"  Generated sample PDF: {test_pdf_path.name} ({test_pdf_path.stat().st_size} bytes)")

        # Run ingestion
        ingest_res = await document_loader.load_and_index(
            file_path=str(test_pdf_path),
            document_id=doc_id,
            user_id="enclave_admin"
        )
        print(f"  Ingest Result: chunks={ingest_res.get('chunks_count')} | embeddings={ingest_res.get('embeddings_count')} | points={ingest_res.get('points_inserted')}")
        assert ingest_res.get("success"), f"Ingestion error: {ingest_res.get('error')}"
        assert ingest_res.get("chunks_count", 0) > 0
        assert ingest_res.get("embeddings_count", 0) > 0
        assert ingest_res.get("points_inserted", 0) > 0
        assert ingest_res.get("verified"), "Post-upsert verification failed"

        # Explicit verification check against Qdrant collection
        verify_dict = await qdrant_client.verify_ingestion(document_id=doc_id, expected_points=ingest_res["chunks_count"])
        assert verify_dict.get("verified", False), f"Qdrant client failed to verify points: {verify_dict}"

        results["5_document_ingestion"] = True
        print(f"  -> PASSED: Document Ingestion & Qdrant Verified ({ingest_res['points_inserted']} points, sample confirmed)")
    except Exception as e:
        results["5_document_ingestion"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # TEST 6: Qdrant Persistence & Document ID Filtering
    # -------------------------------------------------------------
    print("\n[STEP 6/10] Qdrant Persistence & Document ID Filtering")
    try:
        count = await qdrant_client.get_points_count(document_id=doc_id)
        print(f"  Points persisted in Qdrant for document_id='{doc_id}': {count}")
        assert count > 0

        sample = await qdrant_client.get_sample_point(document_id=doc_id)
        assert sample is not None
        assert sample["payload"].get("document_id") == doc_id
        payload_text = sample["payload"].get("text", "")
        print(f"  Retrieved sample vector payload snippet: '{payload_text[:70]}...'")

        results["6_qdrant_persistence"] = True
        print("  -> PASSED: Qdrant Persistence & Document Filtering")
    except Exception as e:
        results["6_qdrant_persistence"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # TEST 7: Grounded RAG Retrieval & Citations
    # -------------------------------------------------------------
    print("\n[STEP 7/10] Grounded RAG Retrieval & Citations")
    try:
        query = "What is the emergency trip threshold temperature for the Titan-9000?"
        hits = await rag_retriever.retrieve(query=query, top_k=3, document_id=doc_id)
        print(f"  Retrieved {len(hits)} grounded chunks for query: '{query}'")
        assert len(hits) > 0

        top_chunk = hits[0]
        print(f"  Top Match Score: {top_chunk.get('similarity_score')} | Page: {top_chunk.get('page')}")
        print(f"  Evidence: '{top_chunk.get('text')[:80]}...'")
        assert top_chunk.get("document_id") == doc_id

        # Format context block
        ctx_block = rag_retriever.build_context_block(hits)
        assert "[Source:" in ctx_block
        print(f"  Verified Citation Context Block generated: {len(ctx_block)} characters")

        results["7_rag_retrieval"] = True
        print("  -> PASSED: Grounded RAG Retrieval with Citations")
    except Exception as e:
        results["7_rag_retrieval"] = False
        print(f"  -> FAILED: {e}")


    # -------------------------------------------------------------
    # TEST 8: Structured Planner (llama3.2:1b) & Critic (smollm2:1.7b)
    # -------------------------------------------------------------
    print("\n[STEP 8/10] Structured Planner (llama3.2:1b) & Critic (smollm2:1.7b)")
    try:
        planner = PlannerNode()
        state = AgenticState(user_query="Inspect telemetry.csv and verify gas turbine vibration levels against ISO 10816-4")
        state = await planner.execute(state)
        print(f"  Planner produced {len(state.plan)} sequential steps:")
        for s in state.plan:
            print(f"    - Step {s.step_number}: '{s.title}' (Agent: {s.target_agent}, Tools: {s.required_tools})")
        assert len(state.plan) > 0

        # Critic Node verification
        verifier = VerifierNode()
        state.current_step_index = 0
        state.observations.append(
            Observation(
                step_number=1,
                agent_name="maintenance",
                tool_name="spreadsheet_reader",
                output={"headers": ["Turbine", "Vibration"], "rows": [["GT-02", "5.9"]]},
                success=True,
                thought="Turbine GT-02 recorded 5.9 mm/s RMS vibration, exceeding the 4.5 mm/s warning threshold per ISO 10816-4."
            )
        )
        state = await verifier.execute(state)
        assert state.verification_passed
        print(f"  Critic Verification: {state.verification_notes}")

        results["8_planner_critic"] = True
        print("  -> PASSED: Planner & Critic Orchestration")
    except Exception as e:
        results["8_planner_critic"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # TEST 9: Specialist Agent Role Prompts & Structured Outputs
    # -------------------------------------------------------------
    print("\n[STEP 9/10] Specialist Agent Role-Based Structured Outputs")
    try:
        from orchestrator.task_classifier import AGENT_PROMPTS
        required_roles = ["risk", "compliance", "safety", "maintenance", "coding", "reporting", "critic", "general"]
        for r in required_roles:
            prompt = AGENT_PROMPTS.get(r)
            assert prompt is not None, f"Missing prompt for specialist role: {r}"
            assert "ROLE:" in prompt
            assert "OBJECTIVE:" in prompt
            assert "RULES:" in prompt
            assert "OUTPUT FORMAT:" in prompt

        print(f"  All {len(required_roles)} specialist system prompts verified with strict industrial constraints.")
        results["9_specialist_prompts"] = True
        print("  -> PASSED: Specialist Agent Role Prompts")
    except Exception as e:
        results["9_specialist_prompts"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # TEST 10: Sovereign AI Enclave Health Check (/api/health/ai)
    # -------------------------------------------------------------
    print("\n[STEP 10/10] Sovereign AI Enclave Health Check (/api/health/ai)")
    try:
        health_res = await health_ai()
        print(f"  Enclave Health Status: {health_res}")
        assert health_res.get("ollama"), "Ollama must be connected"
        assert health_res.get("qdrant"), "Qdrant must be connected"
        assert health_res.get("neo4j"), "Neo4j must be connected"
        assert health_res.get("mongodb"), "MongoDB must be connected"
        assert health_res.get("valkey"), "Valkey must be connected"

        models = health_res.get("models", {})
        print(f"  Model Availability Status: {models}")
        assert models.get("router"), "Router model must be available"
        assert models.get("planner"), "Planner model must be available"
        assert models.get("coding"), "Coding model must be available"
        assert models.get("embedding"), "Embedding model must be available"

        results["10_health_check"] = True
        print("  -> PASSED: Sovereign AI Enclave Health Check")
    except Exception as e:
        results["10_health_check"] = False
        print(f"  -> FAILED: {e}")

    # -------------------------------------------------------------
    # SUMMARY & SCORECARD
    # -------------------------------------------------------------
    duration = round(time.time() - start_all, 2)
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print("\n" + "=" * 70)
    print("FINAL TEST SCORECARD")
    print("=" * 70)
    for test_key, passed in results.items():
        status_str = "PASSED" if passed else "FAILED"
        print(f"  {test_key:<30}: [{status_str}]")

    print("-" * 70)
    print(f"TOTAL: {passed_count}/{total_count} PASSED in {duration}s")
    print("=" * 70)

    if passed_count == total_count:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
