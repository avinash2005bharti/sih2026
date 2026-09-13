"""
Test script to independently verify Moondream vision service via local Ollama.
"""

import sys
import asyncio
from pathlib import Path

ai_services_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ai_services_path))

from vision.vision_service import vision_service

async def main():
    print("=== Testing Vision Service (Moondream) Independently ===")

    test_img = ai_services_path / "workspace" / "test_equipment_label.png"
    if not test_img.exists():
        print(f"Error: {test_img} does not exist.")
        return

    print(f"Checking if vision model '{vision_service.model}' is ready in Ollama...")
    is_ready = await vision_service.is_model_ready()
    print(f"Vision model ready: {is_ready}")

    print("Sending image to Moondream for visual scene analysis...")
    result = await vision_service.analyze_visual_scene(str(test_img))

    print(f"Success: {result.get('success')}")
    print(f"Model used: {result.get('model')}")
    print(f"Duration: {result.get('duration_seconds')}s")
    print(f"Visual description:\n{result.get('description')}")

    assert result.get("success") is True, f"Vision analysis failed: {result.get('error')}"
    assert len(result.get("description", "")) > 10, "Visual description too short!"
    print("[PASS] Test 2 (Independent Vision - Moondream) PASSED successfully!")

if __name__ == "__main__":
    asyncio.run(main())
