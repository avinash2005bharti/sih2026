"""
Test script to independently verify PaddleOCR text extraction and CPU fallback.
"""

import sys
import os
from pathlib import Path

# Add AI-SERVICES root to python path
ai_services_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ai_services_path))

from PIL import Image, ImageDraw, ImageFont
from ocr.ocr_service import ocr_service

def create_synthetic_test_image() -> str:
    """Create a synthetic industrial equipment nameplate image for testing."""
    img = Image.new("RGB", (600, 240), color=(240, 242, 245))
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle([(10, 10), (590, 230)], outline=(50, 60, 70), width=3)

    # Use default font
    draw.text((30, 30), "Equipment ID: P-101", fill=(10, 20, 30))
    draw.text((30, 80), "Pressure: 12.5 bar", fill=(10, 20, 30))
    draw.text((30, 130), "Temperature: 85 C", fill=(10, 20, 30))
    draw.text((30, 180), "Status: Warning", fill=(180, 20, 20))

    test_dir = ai_services_path / "workspace"
    test_dir.mkdir(parents=True, exist_ok=True)
    img_path = str(test_dir / "test_equipment_label.png")
    img.save(img_path)
    return img_path

def main():
    print("=== Testing OCR Service Independently ===")
    img_path = create_synthetic_test_image()
    print(f"Generated test image at: {img_path}")

    print("Running OCR extraction...")
    result = ocr_service.extract_text(img_path)

    print(f"Success: {result.get('success')}")
    print(f"Engine: {result.get('engine')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Text extracted:\n{result.get('text')}")
    print(f"Blocks detected: {len(result.get('blocks', []))}")
    for i, b in enumerate(result.get('blocks', [])):
        print(f"  Block {i+1}: '{b['text']}' (conf: {b['confidence']}, bbox: {b['bbox']})")

    assert result.get("success") is True, "OCR extraction failed!"
    assert "P-101" in result.get("text"), "P-101 not found in OCR text!"
    assert "12.5" in result.get("text") or "bar" in result.get("text"), "Pressure not found in OCR text!"
    print("[PASS] Test 1 (Independent OCR) PASSED successfully!")

if __name__ == "__main__":
    main()
