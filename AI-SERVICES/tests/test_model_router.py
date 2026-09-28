import pytest
from llm.model_router import model_router

def test_route_vision_task():
    decision = model_router.route("Analyze this machine image and check for rust on the valve")
    assert decision.selected_model in ["qwen3-vl:4b", "qwen2.5vl:3b"]
    assert decision.task_capabilities.requires_vision is True

def test_route_excel_task():
    decision = model_router.route("Create an Excel maintenance tracker for turbine bearings")
    # Section 2 & 17: Spreadsheet Agent + openpyxl, NOT coder!
    assert decision.selected_model in ["qwen2.5:1.5b", "qwen3:4b"]
    assert decision.task_capabilities.requires_tools is True

def test_route_complex_planning():
    decision = model_router.route("Create a professional maintenance inspection PDF report from this data and calculate MTTR")
    assert decision.planner_model == "qwen3:4b"
    assert decision.task_capabilities.complexity == "high"

def test_route_fast_classification():
    decision = model_router.route("What is standard operating procedure for shift handover?")
    assert decision.selected_model in ["qwen2.5:3b", "qwen2.5:1.5b"]
