import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator.graph import agentic_workflow
from tools.tool_manager import tool_manager
from rag.qdrant_client import qdrant_service
from rag.chunker import document_chunker
from tools.validators.pdf_validator import validate_pdf_artifact
from tools.validators.xlsx_validator import validate_xlsx_artifact
from core.logging import logger

async def run_demo_1():
    print("\n" + "="*70)
    print("DEMO SCENARIO 1: Maintenance Inspection Analysis & Risk Identification")
    print("="*70)
    prompt = "Analyze this maintenance inspection report and identify major risks for Turbine T-800."
    state = await agentic_workflow.run(
        user_request=prompt,
        conversation_id="demo_scenario_1",
        user_id="analyst_user",
        user_role="analyst"
    )
    print(f"Workflow Complete: Objective={state.task_contract.objective}")
    print(f"Response Summary:\n{state.final_response[:250]}...")
    assert len(state.final_response) > 50

async def run_demo_2():
    print("\n" + "="*70)
    print("DEMO SCENARIO 2: Professional PDF Generation with Artifact Verification")
    print("="*70)
    prompt = "Create a professional maintenance inspection report PDF from this document."
    state = await agentic_workflow.run(
        user_request=prompt,
        conversation_id="demo_scenario_2",
        user_id="engineer_user",
        user_role="engineer"
    )
    print(f"Artifacts Generated: {len(state.artifacts)}")
    for a in state.artifacts:
        print(f"  - [{a['type'].upper()}] {a['filename']} ({a['path']})")
        val = validate_pdf_artifact(a['path'])
        print(f"    Verification: Valid={val['valid']} | Score={val['score']}% | Pages={val['metadata']['page_count']}")
        assert val['valid'] is True

async def run_demo_3():
    print("\n" + "="*70)
    print("DEMO SCENARIO 3: Excel Maintenance Tracker with Formula Verification")
    print("="*70)
    prompt = "Create an Excel maintenance tracker for rotating equipment."
    state = await agentic_workflow.run(
        user_request=prompt,
        conversation_id="demo_scenario_3",
        user_id="operator_user",
        user_role="operator"
    )
    print(f"Artifacts Generated: {len(state.artifacts)}")
    for a in state.artifacts:
        print(f"  - [{a['type'].upper()}] {a['filename']} ({a['path']})")
        val = validate_xlsx_artifact(a['path'])
        print(f"    Verification: Valid={val['valid']} | Score={val['score']}% | Rows={val['metadata']['row_count']}")
        assert val['valid'] is True

async def run_demo_4():
    print("\n" + "="*70)
    print("DEMO SCENARIO 4: Vision Agent Multimodal Equipment Inspection")
    print("="*70)
    prompt = "Analyze this equipment image and check for surface cracks or thermal discoloration."
    state = await agentic_workflow.run(
        user_request=prompt,
        conversation_id="demo_scenario_4",
        user_id="engineer_user",
        user_role="engineer"
    )
    print(f"Vision Complete: Objective={state.task_contract.objective}")
    print(f"Observations:\n{state.final_response[:250]}...")
    assert len(state.final_response) > 20

async def run_demo_5():
    print("\n" + "="*70)
    print("DEMO SCENARIO 5: SOP Ingestion with Verified Qdrant Retrieval")
    print("="*70)
    sop_content = (
        "# High-Pressure Steam Valve Standard Operating Procedure (SOP-502)\n\n"
        "## Emergency Shutdown Procedure\n"
        "In case of main steam line pressure exceeding 180 bar, trigger trip valve XV-101 immediately. "
        "Engage nitrogen purge within 45 seconds to displace residual superheated vapors. "
        "Notify the central control room and isolate manual bypass valve MV-12."
    )
    chunks = document_chunker.chunk_document(
        text=sop_content,
        document_id="sop_502_steam_valve",
        document_name="SOP-502_Steam_Valve.pdf"
    )
    upsert_res = await qdrant_service.upsert_chunks_verified(
        chunks=chunks,
        collection_name="sovereign_demo_knowledge"
    )
    print(f"Qdrant Ingestion: Success={upsert_res['success']} | Verified={upsert_res['verified']} | Points={upsert_res['inserted_count']}")
    
    hits = await qdrant_service.search(
        query="What is the emergency shutdown procedure for high steam pressure?",
        collection_name="sovereign_demo_knowledge",
        limit=2
    )
    print(f"Retrieval Hits: {len(hits)}")
    for h in hits:
        print(f"  - Grounded Excerpt: {h['text'][:120]}...")
    assert len(hits) > 0
    assert any("trip valve" in h["text"].lower() for h in hits)

async def main():
    print("="*70)
    print("RUNNING ALL 5 VERIFIED DEMO SCENARIOS ON LOCAL WORKBENCH")
    print("="*70)
    await run_demo_1()
    await run_demo_2()
    await run_demo_3()
    await run_demo_4()
    await run_demo_5()
    print("\n" + "="*70)
    print("ALL 5 DEMO SCENARIOS EXECUTED & VERIFIED SUCCESSFULLY!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
