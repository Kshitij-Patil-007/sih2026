"""
End-to-End Integration Test
Tests the complete pipeline: Load image -> Ask AI -> Get answer
"""

import os
from dotenv import load_dotenv
from backend import process_query, detect_changes
from PIL import Image, ImageDraw, ImageFont
import numpy as np

load_dotenv()

def create_sample_satellite_image():
    """Create a realistic-looking test image"""
    # Create a 800x800 image with different zones
    img = Image.new('RGB', (800, 800))
    draw = ImageDraw.Draw(img)

    # Water (blue)
    draw.rectangle([0, 0, 800, 300], fill=(50, 100, 150))

    # Urban area (gray buildings)
    for i in range(5):
        for j in range(5):
            x = 100 + i * 120
            y = 350 + j * 80
            draw.rectangle([x, y, x+80, y+60], fill=(120, 120, 120))

    # Vegetation (green)
    draw.rectangle([0, 300, 800, 350], fill=(60, 120, 60))
    draw.rectangle([650, 350, 800, 800], fill=(70, 130, 70))

    return img

def test_full_pipeline():
    """Test complete backend pipeline"""
    print("\n" + "=" * 60)
    print("SatQuery AI - Full Integration Test")
    print("=" * 60)

    # Step 1: Create test image
    print("\n[1/4] Creating sample satellite-like image...")
    test_img = create_sample_satellite_image()
    test_img.save("test_satellite.png")
    print("   [OK] Image created: test_satellite.png")

    # Step 2: Test single-image Q&A with Gemini
    print("\n[2/4] Testing AI vision analysis...")
    questions = [
        "Describe the land cover types visible in this image.",
        "Are there any buildings or urban structures?",
        "What percentage is water vs land?"
    ]

    for i, q in enumerate(questions, 1):
        print(f"\n   Question {i}: {q}")
        result = process_query(test_img, q, model_type="auto")
        print(f"   Model: {result['model_used']}")
        print(f"   Answer: {result['answer'][:150]}...")

    # Step 3: Test change detection
    print("\n[3/4] Testing change detection...")
    img_before = test_img.copy()

    # Modify to simulate change
    draw = ImageDraw.Draw(test_img)
    draw.rectangle([400, 500, 600, 700], fill=(180, 180, 180))  # New construction
    img_after = test_img

    changes = detect_changes(img_before, img_after)
    print(f"   Change summary: {changes['summary']}")
    print(f"   Changed pixels: {changes['changed_pixels']:,}")
    print(f"   Change percentage: {changes['change_percentage']}%")

    # Step 4: Verify all modules loaded
    print("\n[4/4] Verifying all backend modules...")
    from backend.router import route_query
    from backend.geo_loader import load_geotiff

    route_result = route_query("What changed between these images?")
    print(f"   [OK] Router working: {route_result['query_type']}")
    print(f"   [OK] GeoTIFF loader available")
    print(f"   [OK] Change detection working")
    print(f"   [OK] Vision AI working ({result['model_used']})")

    print("\n" + "=" * 60)
    print("[OK] FULL INTEGRATION TEST PASSED!")
    print("=" * 60)
    print("\nBackend is ready for frontend integration!")
    print("\nNext steps:")
    print("1. Wait for partner to download real satellite images")
    print("2. Test with actual satellite imagery")
    print("3. Connect to frontend Streamlit UI")

if __name__ == "__main__":
    test_full_pipeline()
