import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from rag.document_store import document_store
from memory.context_builder import central_context_builder, QueryIntent
from orchestrator.task_classifier import task_classifier
from orchestrator.nodes.planner import PlannerNode
from orchestrator.nodes.executor import ExecutorNode
from orchestrator.state import AgenticState

async def run_tests():
    print("=== TEST 1: document_store.list_documents for non-admin ===")
    docs = document_store.list_documents(user_id="6aa69e6b368643be8d439999", is_admin=False)
    print("Non-admin documents count:", len(docs))
    assert len(docs) == 0, f"Expected 0 documents for non-admin, got {len(docs)}: {[d.get('name') for d in docs]}"
    print("PASSED: Non-admin sees 0 documents.")

    print("\n=== TEST 2: context_builder.classify_intent ===")
    queries = [
        "give me any document",
        "give me the document",
        "show me document",
        "what documents do i have",
        "read document"
    ]
    for q in queries:
        intent = central_context_builder.classify_intent(q)
        print(f"Query: '{q}' -> Intent: {intent.value}")
        assert intent == QueryIntent.DOCUMENT_METADATA_QUERY, f"Failed for '{q}': got {intent}"
    print("PASSED: All document retrieval queries classified correctly.")

    print("\n=== TEST 3: context_builder.build with 0 documents for non-admin ===")
    ctx = await central_context_builder.build(
        conversation_id="test_conv",
        user_id="6aa69e6b368643be8d439999",
        is_admin=False,
        query="give me any document"
    )
    prompt = ctx.system_prompt
    print("Checking prompt for anti-hallucination directive...")
    assert "Total Documents in Workspace: 0" in prompt, "Expected 0 documents in prompt"
    assert "Under NO circumstances should you fabricate, hallucinate, or synthesize a Standard Operating Procedure (SOP)" in prompt, "Missing anti-SOP hallucination directive"
    print("PASSED: Prompt forbids SOP hallucination when 0 documents exist.")

    print("\n=== TEST 4: task_classifier ===")
    tc = task_classifier.classify("give me any document")
    print("Classification for 'give me any document':", tc.task_type, tc.agent)
    assert tc.task_type == "document_crud", f"Expected document_crud, got {tc.task_type}"
    assert tc.agent == "document_agent", f"Expected document_agent, got {tc.agent}"
    print("PASSED: Task classified as document_crud.")

    print("\n=== TEST 5: planner node ===")
    planner = PlannerNode()
    state = AgenticState(user_query="give me any document")
    planned_state = await planner.execute(state)
    print("Planned steps count:", len(planned_state.plan))
    for s in planned_state.plan:
        print(f"  Step {s.step_number}: {s.title} (agent: {s.target_agent}, tools: {s.required_tools})")
    assert len(planned_state.plan) == 2, f"Expected 2 steps, got {len(planned_state.plan)}"
    assert "docx_generator" not in planned_state.plan[0].required_tools
    assert "pdf_generator" not in planned_state.plan[-1].required_tools
    assert planned_state.plan[0].title == "Retrieve & Inspect Document"
    print("PASSED: Planner creates inspection steps, NOT document generation.")

    print("\n=== TEST 6: executor node synthesis ===")
    executor = ExecutorNode()
    gen_state = AgenticState(user_query="give me any document")
    content = executor._synthesize_document_content(gen_state, "Requested Document")
    print("Synthesized content sample (first 200 chars):", repr(content[:200]))
    assert "Main Bearing Vibration" not in content, "SOP bearing vibration should not be hardcoded for non-SOP queries"
    assert "Lockout/Tagout (LOTO)" not in content, "LOTO should not be hardcoded for non-SOP queries"
    assert "Sovereign Technical Report" in content or "Requested Document" in content
    print("PASSED: Executor does not synthesize hardcoded SOP for generic queries.")

    print("\n=== ALL 6 TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
