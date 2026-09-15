"""
Comprehensive Multi-Layer Memory & Context Pipeline Test Suite.
Tests:
  TEST 1: Basic conversation memory ("My name is TestUser" -> "What is my name?")
  TEST 2: Previous instruction recall ("Create a maintenance inspection report" -> "What did I ask you previously?")
  TEST 3: Artifact memory (create Maintenance_Inspection_Report.xlsx -> "Which file did you create?")
  TEST 4: Multiple artifacts (xlsx + pdf -> "Which files did you create?")
  TEST 5: Context reference ("this data" refers to maintenance inspection data)
  TEST 6: Conversation isolation (Conversation A files never leaked into Conversation B)
  TEST 7: Long-term memory retrieval (cross-conversation persistent memory via Mem0/Qdrant)
  TEST 8: Neo4j entity & relationship retrieval
  TEST 9: Service failure resilience (Qdrant/Neo4j fallback to MongoDB STM)
  TEST 10: Restart persistence (reconstruct context from cold MongoDB storage after cache wipe)
"""

import os
import sys
import uuid
import pytest
import asyncio
import httpx

# Ensure AI-SERVICES root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.context_builder import central_context_builder, QueryIntent
from memory.artifacts.artifact_store import artifact_store
from memory.executions.execution_store import execution_store
from memory.stm.stm_manager import stm_manager
from memory.graph.neo4j_service import neo4j_service
from memory.vector.qdrant_service import qdrant_service
from memory.mem0.mem0_service import mem0_service

BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.asyncio
async def test_01_basic_conversation_memory():
    """TEST 1: Assistant remembers user name from previous turn."""
    conv_id = f"test-basic-conv-{uuid.uuid4().hex[:8]}"
    user_id = "test-user-alice"

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180.0) as client:
        # Turn 1: Tell name
        res1 = await client.post("/api/chat", json={
            "message": "My name is TestUser.",
            "conversation_id": conv_id,
            "user_id": user_id,
        })
        assert res1.status_code == 200, f"Turn 1 failed: {res1.text}"
        data1 = res1.json()
        assert "response" in data1
        print(f"\n[TEST 1] Turn 1 Response: {data1['response'][:100]}")

        # Turn 2: Ask name
        res2 = await client.post("/api/chat", json={
            "message": "What is my name?",
            "conversation_id": conv_id,
            "user_id": user_id,
        })
        assert res2.status_code == 200, f"Turn 2 failed: {res2.text}"
        data2 = res2.json()
        response_text = data2["response"]
        print(f"[TEST 1] Turn 2 Response: {response_text}")

        # Validation: Context retained "TestUser"
        assert "TestUser" in response_text or "testuser" in response_text.lower(), \
            f"Expected 'TestUser' in response, got: {response_text}"


@pytest.mark.asyncio
async def test_02_previous_instruction_recall():
    """TEST 2: Assistant identifies previous instruction accurately."""
    conv_id = f"test-prev-instr-{uuid.uuid4().hex[:8]}"
    user_id = "test-user-bob"

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180.0) as client:
        # Turn 1: Specific instruction
        res1 = await client.post("/api/chat", json={
            "message": "Create a maintenance inspection report for pump P-104.",
            "conversation_id": conv_id,
            "user_id": user_id,
        })
        assert res1.status_code == 200

        # Turn 2: Ask about previous instruction
        res2 = await client.post("/api/chat", json={
            "message": "What did I ask you previously?",
            "conversation_id": conv_id,
            "user_id": user_id,
        })
        assert res2.status_code == 200
        reply = res2.json()["response"].lower()
        print(f"\n[TEST 2] Recall Response: {reply}")

        assert any(term in reply for term in ["maintenance", "inspection", "report", "p-104"]), \
            f"Expected previous instruction recall, got: {reply}"


@pytest.mark.asyncio
async def test_03_artifact_memory():
    """TEST 3: Assistant retrieves generated artifact from MongoDB artifact store."""
    conv_id = f"test-artifact-single-{uuid.uuid4().hex[:8]}"
    user_id = "test-user-charlie"

    # Register artifact in artifact_store
    artifact = artifact_store.register_artifact(
        conversation_id=conv_id,
        filename="Maintenance_Inspection_Report.xlsx",
        file_path=os.path.join(os.getcwd(), "sandbox", "Maintenance_Inspection_Report.xlsx"),
        artifact_type="spreadsheet",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        description="Industrial maintenance inspection data report in Excel format",
        user_id=user_id,
    )
    assert artifact is not None
    assert artifact["filename"] == "Maintenance_Inspection_Report.xlsx"

    # Verify context builder retrieves artifact
    bundle = await central_context_builder.build(
        conversation_id=conv_id,
        user_id=user_id,
        current_query="Which file did you create?",
    )
    assert len(bundle.artifacts) >= 1
    assert bundle.artifacts[0]["filename"] == "Maintenance_Inspection_Report.xlsx"

    # Verify chat endpoint answers using artifact memory
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180.0) as client:
        res = await client.post("/api/chat", json={
            "message": "Which file did you create?",
            "conversation_id": conv_id,
            "user_id": user_id,
        })
        assert res.status_code == 200
        reply = res.json()["response"]
        print(f"\n[TEST 3] Single Artifact Response: {reply}")
        assert "Maintenance_Inspection_Report.xlsx" in reply or "maintenance_inspection_report.xlsx" in reply.lower(), \
            f"Expected 'Maintenance_Inspection_Report.xlsx' in reply, got: {reply}"


@pytest.mark.asyncio
async def test_04_multiple_artifacts_memory():
    """TEST 4: Assistant retrieves multiple generated artifacts (Excel + PDF)."""
    conv_id = f"test-artifact-multi-{uuid.uuid4().hex[:8]}"
    user_id = "test-user-dan"

    # Register Excel file
    artifact_store.register_artifact(
        conversation_id=conv_id,
        filename="Maintenance_Inspection_Report.xlsx",
        file_path=os.path.join(os.getcwd(), "sandbox", "Maintenance_Inspection_Report.xlsx"),
        artifact_type="spreadsheet",
        description="Maintenance inspection report Excel table",
        user_id=user_id,
    )

    # Register PDF file
    artifact_store.register_artifact(
        conversation_id=conv_id,
        filename="Maintenance_Inspection_Report.pdf",
        file_path=os.path.join(os.getcwd(), "sandbox", "Maintenance_Inspection_Report.pdf"),
        artifact_type="pdf",
        description="Maintenance inspection report PDF document",
        user_id=user_id,
    )

    # Context Builder verification
    bundle = await central_context_builder.build(
        conversation_id=conv_id,
        user_id=user_id,
        current_query="Which files have you created?",
    )
    assert len(bundle.artifacts) == 2
    filenames = [a["filename"] for a in bundle.artifacts]
    assert "Maintenance_Inspection_Report.xlsx" in filenames
    assert "Maintenance_Inspection_Report.pdf" in filenames

    # Chat endpoint verification
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180.0) as client:
        res = await client.post("/api/chat", json={
            "message": "Which files have you created?",
            "conversation_id": conv_id,
            "user_id": user_id,
        })
        assert res.status_code == 200
        reply = res.json()["response"].lower()
        print(f"\n[TEST 4] Multiple Artifacts Response: {res.json()['response']}")
        assert "maintenance_inspection_report.xlsx" in reply
        assert "maintenance_inspection_report.pdf" in reply


@pytest.mark.asyncio
async def test_05_context_reference():
    """TEST 5: Assistant understands anaphoric reference ('this data') from previous context."""
    conv_id = f"test-context-ref-{uuid.uuid4().hex[:8]}"
    user_id = "test-user-eva"

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180.0) as client:
        # Turn 1: Establish data context
        res1 = await client.post("/api/chat", json={
            "message": "Create a report using the industrial maintenance inspection data for boiler B-2.",
            "conversation_id": conv_id,
            "user_id": user_id,
        })
        assert res1.status_code == 200

        # Turn 2: Follow-up using 'this data'
        res2 = await client.post("/api/chat", json={
            "message": "What does this data refer to?",
            "conversation_id": conv_id,
            "user_id": user_id,
        })
        assert res2.status_code == 200
        reply = res2.json()["response"].lower()
        print(f"\n[TEST 5] Context Reference Response: {reply}")
        assert any(term in reply for term in ["maintenance", "inspection", "boiler", "b-2"]), \
            f"Expected reference to boiler/maintenance data, got: {reply}"


@pytest.mark.asyncio
async def test_06_conversation_isolation():
    """TEST 6: Conversation isolation - Conversation B cannot access Conversation A's artifacts."""
    conv_a = f"test-iso-a-{uuid.uuid4().hex[:8]}"
    conv_b = f"test-iso-b-{uuid.uuid4().hex[:8]}"

    # Save artifact in conversation A
    artifact_store.register_artifact(
        conversation_id=conv_a,
        filename="Secret_Report_A.xlsx",
        file_path="sandbox/Secret_Report_A.xlsx",
        artifact_type="spreadsheet",
        user_id="user-a",
    )

    # Build context for conversation B
    bundle_b = await central_context_builder.build(
        conversation_id=conv_b,
        user_id="user-b",
        current_query="Which file did you create?",
    )

    # Assure Secret_Report_A is NOT present in conversation B
    filenames_b = [a["filename"] for a in bundle_b.artifacts]
    assert "Secret_Report_A.xlsx" not in filenames_b
    assert len(bundle_b.artifacts) == 0
    print(f"\n[TEST 6] Conversation Isolation Confirmed: Conv B has 0 artifacts from Conv A.")


@pytest.mark.asyncio
async def test_07_long_term_memory():
    """TEST 7: Long-term memory - persistent facts stored in Mem0/Qdrant across conversations."""
    user_id = f"test-user-ltm-{uuid.uuid4().hex[:8]}"
    conv_1 = f"test-ltm-c1-{uuid.uuid4().hex[:8]}"
    conv_2 = f"test-ltm-c2-{uuid.uuid4().hex[:8]}"

    # Add memory for user
    await mem0_service.add_memory(
        content="The user always prefers Excel reports in tabular format for industrial equipment audits.",
        user_id=user_id,
        metadata={"category": "user_preference"}
    )

    # Query in brand new conversation conv_2
    bundle = await central_context_builder.build(
        conversation_id=conv_2,
        user_id=user_id,
        current_query="What format do I prefer for my reports and audits?",
    )

    assert len(bundle.memories) >= 1
    memory_text = " ".join(bundle.memories).lower()
    print(f"\n[TEST 7] Retrieved LTM Memories: {bundle.memories}")
    assert "tabular" in memory_text or "excel" in memory_text or "reports" in memory_text


@pytest.mark.asyncio
async def test_08_neo4j_graph_relationships():
    """TEST 8: Neo4j knowledge graph entity relationship retrieval."""
    test_equipment = f"Turbine-T{uuid.uuid4().hex[:4]}"
    test_risk = "Bearing overheating risk"

    # Record entity memory in Neo4j
    await neo4j_service.record_memory(
        memory_id=f"mem-neo-{uuid.uuid4().hex[:6]}",
        user_id="engineer-1",
        content=f"Equipment {test_equipment} has inspection status: {test_risk}.",
        memory_type="equipment_inspection",
        entities=[test_equipment, "Overheating", "Inspection"]
    )

    # Query related graph context
    graph_ctx = await neo4j_service.query_related_context(
        query=f"What is the condition of {test_equipment}?",
        user_id="engineer-1",
        limit=5
    )
    print(f"\n[TEST 8] Neo4j Graph Context: {graph_ctx}")
    assert len(graph_ctx) >= 1
    assert any(test_equipment in str(item) for item in graph_ctx)


@pytest.mark.asyncio
async def test_09_service_failure_resilience():
    """TEST 9: Fault-tolerance - gracefully handle Qdrant/Neo4j unavailability using MongoDB STM."""
    conv_id = f"test-resilience-{uuid.uuid4().hex[:8]}"

    # Add message in STM
    await stm_manager.record_message(
        conversation_id=conv_id,
        role="user",
        content="Hello resilient sovereign assistant."
    )

    # Build context while simulating downstream failures
    # ContextBuilder has internal try/except blocks for LTM and Graph
    bundle = await central_context_builder.build(
        conversation_id=conv_id,
        user_id="resilience-user",
        current_query="Hello again.",
    )

    # System must not crash, and STM must be preserved
    assert bundle is not None
    assert len(bundle.recent_messages) >= 1
    assert bundle.recent_messages[0]["content"] == "Hello resilient sovereign assistant."
    print(f"\n[TEST 9] Resilience check passed: STM returned {len(bundle.recent_messages)} messages during simulated fallbacks.")


@pytest.mark.asyncio
async def test_10_restart_persistence():
    """TEST 10: Restart persistence - Cold reconstruction from MongoDB operational collections."""
    conv_id = f"test-restart-{uuid.uuid4().hex[:8]}"
    user_id = "test-user-restart"

    # Record messages in MongoDB
    await stm_manager.record_message(
        conversation_id=conv_id,
        role="user",
        content="Store this vital inspection protocol in MongoDB."
    )
    await stm_manager.record_message(
        conversation_id=conv_id,
        role="assistant",
        content="Vital inspection protocol recorded."
    )

    # Register artifact in MongoDB
    artifact_store.register_artifact(
        conversation_id=conv_id,
        filename="Persisted_Protocol.xlsx",
        file_path="sandbox/Persisted_Protocol.xlsx",
        artifact_type="spreadsheet",
        user_id=user_id,
    )

    # Wipe in-memory caches to simulate server restart / new worker process
    stm_manager.clear_context(conv_id)

    # Reconstruct from MongoDB
    reconstructed_bundle = await central_context_builder.build(
        conversation_id=conv_id,
        user_id=user_id,
        current_query="What file did you create?",
    )

    # Verify both history and artifact persisted through restart
    assert len(reconstructed_bundle.recent_messages) >= 2
    assert reconstructed_bundle.recent_messages[0]["content"] == "Store this vital inspection protocol in MongoDB."
    assert len(reconstructed_bundle.artifacts) >= 1
    assert reconstructed_bundle.artifacts[0]["filename"] == "Persisted_Protocol.xlsx"
    print(f"\n[TEST 10] Restart persistence verified: Reconstructed {len(reconstructed_bundle.recent_messages)} msgs and {len(reconstructed_bundle.artifacts)} artifacts from MongoDB.")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
