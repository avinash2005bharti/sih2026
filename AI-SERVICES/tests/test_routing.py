from llm.model_router import model_router

def test_routing_rules():
    assert model_router.route("Hello, how are you?") == "qwen2.5:1.5b"
    assert model_router.route("Write a Python program to calculate average temperature.") == "qwen2.5-coder:1.5b"
    assert model_router.route("Analyze this image.") == "moondream:latest"
    assert model_router.route("Extract all text from this scanned document.") == "PYTHON_OCR"
    assert model_router.route("Find previous maintenance incidents related to this equipment.") == "qwen2.5:1.5b"
    assert model_router.route("Create an Excel report from this data.") == "qwen2.5-coder:1.5b"
    assert model_router.route("Create a folder called Reports and save the report inside it.") == "qwen2.5-coder:1.5b"

if __name__ == "__main__":
    test_routing_rules()
    print("All model routing tests passed!")
