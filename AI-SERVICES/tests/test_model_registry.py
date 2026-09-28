import pytest
from llm.model_registry import model_registry, ModelMetadata

def test_model_registry_defaults():
    models = model_registry.list_models()
    names = [m.name for m in models]
    
    assert "qwen3:4b" in names
    assert "qwen2.5-coder:3b" in names
    assert "qwen2.5vl:3b" in names
    assert "nomic-embed-text:latest" in names

def test_planner_capabilities():
    planner = model_registry.get_model("qwen3:4b")
    assert planner is not None
    assert "planning" in planner.capabilities
    assert "task_decomposition" in planner.capabilities
    assert planner.vram_estimate_mb <= 3000

def test_coder_capabilities():
    coder = model_registry.get_model("qwen2.5-coder:3b")
    assert coder is not None
    assert "coding" in coder.capabilities
    assert "complex_coding" in coder.capabilities

def test_vram_estimation():
    total_vram = model_registry.estimate_vram_mb(["qwen3:4b"])
    assert 2000 <= total_vram <= 3000

def test_fallback_resolution():
    fallback = model_registry.get_fallback("qwen2.5:3b")
    assert fallback == "qwen2.5:1.5b"
