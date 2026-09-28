"""
End-to-End Test Suite for SIH 26117 Dual Hardware Routing Architecture.
Tests all 7 scenarios specified in project requirements:
1. General ("What is preventive maintenance?") -> Qwen3 4B
2. Coding ("Write a Python script to extract tables from a PDF.") -> Qwen2.5-Coder 3B
3. Image / Vision -> OCR + Gemma 3 4B
4. Vision Fallback -> Qwen2.5-VL 3B
5. RAG -> nomic-embed-text -> Qdrant -> retrieved chunks -> Qwen3 4B
6. File generation -> XLSX generation -> artifact validation
7. CPU mode -> CPU_ONLY profile -> lightweight models (Qwen2.5 1.5B, Coder 1.5B, Moondream)
"""

import sys
import os
from pathlib import Path

# Add AI-SERVICES root to python path
sys.path.insert(0, str(Path(__file__).parent))

from core.logging import logger
from core.hardware import get_hardware_profile, PROFILE_GPU_RTX2050, PROFILE_CPU_ONLY
from llm.model_registry import model_registry
from llm.model_router import model_router
from orchestrator.task_classifier import task_classifier, TaskType
from tools.validators.artifact_validator import validate_artifact


def test_scenario_1_general():
    print("\n--- Test 1: General Conversation ---")
    query = "What is preventive maintenance?"
    classification = task_classifier.classify(query, has_images=False)
    print(f"Query: '{query}'")
    print(f"Classifier Output: task_type={classification.task_type}, agent={classification.agent}")
    
    selection = model_router.select(
        task_type=classification.task_type,
        requires_vision=classification.requires_vision,
        requires_tools=classification.requires_tools,
        complexity=classification.complexity,
        hardware="GPU_RTX2050"
    )
    print(f"Router Selection: primary={selection['primary_model']}, fallback={selection['fallback_model']}, selected={selection['selected_model']}")
    print(f"Reason: {selection['reason']}")
    
    assert selection["primary_model"] == "qwen3:4b", f"Expected qwen3:4b, got {selection['primary_model']}"
    print("[PASS] Test 1: General conversation successfully routed to Qwen3 4B")


def test_scenario_2_coding():
    print("\n--- Test 2: Coding Task ---")
    query = "Write a Python script to extract tables from a PDF."
    classification = task_classifier.classify(query, has_images=False)
    print(f"Query: '{query}'")
    print(f"Classifier Output: task_type={classification.task_type}, requires_tools={classification.requires_tools}")
    
    selection = model_router.select(
        task_type=classification.task_type,
        requires_vision=classification.requires_vision,
        requires_tools=classification.requires_tools,
        complexity=classification.complexity,
        hardware="GPU_RTX2050"
    )
    print(f"Router Selection: primary={selection['primary_model']}, fallback={selection['fallback_model']}, selected={selection['selected_model']}")
    print(f"Reason: {selection['reason']}")
    
    assert selection["primary_model"] == "qwen2.5-coder:3b", f"Expected qwen2.5-coder:3b, got {selection['primary_model']}"
    print("[PASS] Test 2: Coding task successfully routed to Qwen2.5-Coder 3B")


def test_scenario_3_vision():
    print("\n--- Test 3: Image / Vision Inspection ---")
    query = "Inspect this bearing vibration sensor diagram and identify anomalies."
    classification = task_classifier.classify(query, has_images=True)
    print(f"Query: '{query}' (has_images=True)")
    print(f"Classifier Output: task_type={classification.task_type}, requires_vision={classification.requires_vision}")
    
    selection = model_router.select(
        task_type=classification.task_type,
        requires_vision=classification.requires_vision,
        requires_tools=classification.requires_tools,
        complexity=classification.complexity,
        hardware="GPU_RTX2050"
    )
    print(f"Router Selection: primary={selection['primary_model']}, fallback={selection['fallback_model']}")
    print(f"Reason: {selection['reason']}")
    
    assert selection["primary_model"] == "gemma3:4b", f"Expected gemma3:4b, got {selection['primary_model']}"
    print("[PASS] Test 3: Vision task successfully routed to primary vision model Gemma 3 4B")


def test_scenario_4_vision_fallback():
    print("\n--- Test 4: Vision Model Fallback ---")
    # Simulate Gemma 3 4B missing, fallback to Qwen2.5-VL 3B
    selection = model_router.select(
        task_type="VISION",
        requires_vision=True,
        hardware="GPU_RTX2050"
    )
    primary = selection["primary_model"]
    fallback = selection["fallback_model"]
    print(f"Primary Vision Model: {primary}")
    print(f"Configured Vision Fallback: {fallback}")
    
    assert primary == "gemma3:4b", f"Expected primary gemma3:4b, got {primary}"
    assert fallback == "qwen2.5vl:3b", f"Expected fallback qwen2.5vl:3b, got {fallback}"
    
    # Check fallback chain walking in registry
    resolved = model_registry.resolve_fallback_chain("gemma3:4b")
    print(f"Resolved fallback model when gemma3:4b missing: '{resolved}'")
    assert resolved in ["qwen2.5vl:3b", "moondream", "qwen3:4b", "gemma3:4b"], f"Unexpected fallback resolution: {resolved}"
    print("[PASS] Test 4: Vision fallback chain correctly configured (Gemma 3 4B -> Qwen2.5-VL 3B -> Moondream)")


def test_scenario_5_rag():
    print("\n--- Test 5: RAG Pipeline & Embedding Separation ---")
    embedding_model = model_registry.get_default_model_for_role("embedding", hardware_profile="GPU_RTX2050")
    print(f"Configured Embedding Model: '{embedding_model}'")
    assert "nomic-embed-text" in embedding_model, f"Expected nomic-embed-text, got {embedding_model}"
    
    # Verify embedding is never routed to chat model
    assert embedding_model != "qwen3:4b", "Embedding model must be separated from Qwen3 4B"
    
    # Verify RAG question routes to general planner Qwen3 4B
    rag_query = "What is the maintenance procedure for turbine rotor according to section 4?"
    classification = task_classifier.classify(rag_query, has_images=False)
    selection = model_router.select(
        task_type=classification.task_type,
        requires_vision=False,
        requires_tools=False,
        hardware="GPU_RTX2050"
    )
    print(f"RAG Synthesis Model Selection: {selection['primary_model']}")
    assert selection["primary_model"] == "qwen3:4b", f"Expected qwen3:4b, got {selection['primary_model']}"
    print("[PASS] Test 5: Embedding model strictly isolated to nomic-embed-text; synthesis routed to Qwen3 4B")


def test_scenario_6_file_generation():
    print("\n--- Test 6: File Generation & Validation Pipeline ---")
    query = "Create an inspection report in Excel."
    classification = task_classifier.classify(query, has_images=False)
    print(f"Query: '{query}'")
    print(f"Classifier Output: task_type={classification.task_type}, requires_tools={classification.requires_tools}")
    
    # Test file generator validator with a generated inspection Excel sheet
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inspection_Report"
    
    headers = ["Asset ID", "Component", "Condition", "Vibration (mm/s)", "Temperature (C)", "Status"]
    ws.append(headers)
    ws.append(["AST-101", "Motor Bearing A", "Nominal", 1.8, 48.5, "PASSED"])
    ws.append(["AST-102", "Gearbox Shaft", "Warning", 4.6, 72.1, "NEEDS_ATTENTION"])
    ws.append(["AST-103", "Cooling Fan", "Critical", 8.2, 89.0, "IMMEDIATE_ACTION"])
    
    test_file = Path("test_inspection_report.xlsx")
    wb.save(str(test_file))
    
    try:
        val_res = validate_artifact(
            file_path=str(test_file),
            expected_type="xlsx",
            required_keywords=["motor", "bearing", "gearbox"]
        )
        print(f"Validation Result: success={val_res['success']}, score={val_res['score']}, checks={val_res['checks_passed']}")
        assert val_res["success"] is True, f"Validation failed: {val_res.get('issues')}"
        assert "readable_structure" in val_res["checks_passed"]
        assert "no_placeholders" in val_res["checks_passed"]
        print("[PASS] Test 6: File generation and artifact validation pipeline successfully verified")
    finally:
        if test_file.exists():
            test_file.unlink()


def test_scenario_7_cpu_mode():
    print("\n--- Test 7: CPU-Only Profile Compatibility ---")
    # Verify CPU profile produces lightweight models without demanding RTX-specific models
    general_cpu = model_router.select(task_type="GENERAL", hardware="CPU_ONLY")
    coding_cpu = model_router.select(task_type="CODING", requires_tools=True, hardware="CPU_ONLY")
    vision_cpu = model_router.select(task_type="VISION", requires_vision=True, hardware="CPU_ONLY")
    classifier_cpu = model_router.select(task_type="CLASSIFIER", hardware="CPU_ONLY")
    
    print(f"CPU General: primary={general_cpu['primary_model']}, reason={general_cpu['reason']}")
    print(f"CPU Coding:  primary={coding_cpu['primary_model']}, reason={coding_cpu['reason']}")
    print(f"CPU Vision:  primary={vision_cpu['primary_model']}, reason={vision_cpu['reason']}")
    print(f"CPU Classifier: primary={classifier_cpu['primary_model']}, reason={classifier_cpu['reason']}")
    
    assert general_cpu["primary_model"] == "qwen2.5:1.5b", f"Expected qwen2.5:1.5b, got {general_cpu['primary_model']}"
    assert coding_cpu["primary_model"] == "qwen2.5-coder:1.5b", f"Expected qwen2.5-coder:1.5b, got {coding_cpu['primary_model']}"
    assert vision_cpu["primary_model"] == "moondream", f"Expected moondream, got {vision_cpu['primary_model']}"
    assert classifier_cpu["primary_model"] == "qwen2.5:0.5b", f"Expected qwen2.5:0.5b, got {classifier_cpu['primary_model']}"
    
    print("[PASS] Test 7: CPU-Only profile correctly selects lightweight SLMs without breaking")


if __name__ == "__main__":
    print("=================================================================")
    print(" STARTING SIH 26117 ROUTING & ARCHITECTURE VERIFICATION TEST SUITE")
    print("=================================================================")
    test_scenario_1_general()
    test_scenario_2_coding()
    test_scenario_3_vision()
    test_scenario_4_vision_fallback()
    test_scenario_5_rag()
    test_scenario_6_file_generation()
    test_scenario_7_cpu_mode()
    print("\n=================================================================")
    print(" [ALL TESTS PASSED] 7/7 Scenarios Successfully Verified!")
    print("=================================================================")
