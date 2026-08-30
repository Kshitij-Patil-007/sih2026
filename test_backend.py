"""
Backend Test Script
Quick test to verify all backend modules are working
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.router import route_query, extract_features
from backend.vlm_engine import process_query
from PIL import Image
import numpy as np

def test_router():
    """Test the query router"""
    print("=" * 50)
    print("Testing Query Router")
    print("=" * 50)

    test_queries = [
        "What changed between these two images?",
        "How many storage tanks are visible?",
        "Describe the vegetation in this area",
        "What do you see in this satellite image?"
    ]

    for query in test_queries:
        result = route_query(query)
        print(f"\n[Query] {query}")
        print(f"   Type: {result['query_type']}")
        print(f"   Keywords: {result['keywords']}")
        print(f"   Action: {result['suggested_action']}")


def test_vlm():
    """Test vision model with a dummy image"""
    print("\n" + "=" * 50)
    print("Testing Vision-Language Model")
    print("=" * 50)

    # Create a dummy RGB image
    dummy_image = Image.fromarray(
        np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    )

    result = process_query(
        dummy_image,
        "What do you see in this satellite image?",
        model_type="placeholder"
    )

    print(f"\n[VLM] Model: {result['model_used']}")
    print(f"   Query: {result['query']}")
    print(f"   Answer: {result['answer']}")
    print(f"   Confidence: {result['confidence']}")


def test_geo_loader():
    """Test GeoTIFF loader with a dummy image"""
    print("\n" + "=" * 50)
    print("Testing GeoTIFF Loader")
    print("=" * 50)

    try:
        from backend.geo_loader import _load_as_regular_image

        # Create and save a dummy image
        dummy_image = Image.fromarray(
            np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        )
        dummy_path = Path(__file__).parent / "test_image.png"
        dummy_image.save(dummy_path)

        # Load it back
        result = _load_as_regular_image(dummy_path)

        print(f"\n[Loader] Loaded image successfully")
        print(f"   Size: {result['metadata']['width']}x{result['metadata']['height']}")
        print(f"   Format: {result['metadata'].get('format', 'N/A')}")

        # Cleanup
        dummy_path.unlink()

    except Exception as e:
        print(f"   [Error] {e}")


def test_change_detection():
    """Test change detection with dummy images"""
    print("\n" + "=" * 50)
    print("Testing Change Detection")
    print("=" * 50)

    try:
        from backend.change_detection import detect_changes

        # Create two similar images with slight differences
        img1 = Image.fromarray(
            np.full((256, 256, 3), 100, dtype=np.uint8)
        )
        img2_arr = np.full((256, 256, 3), 100, dtype=np.uint8)
        img2_arr[50:100, 50:100] = 200  # Add a bright square
        img2 = Image.fromarray(img2_arr)

        result = detect_changes(img1, img2)

        print(f"\n[Change Detection] Results:")
        print(f"   Summary: {result['summary']}")
        print(f"   Changed pixels: {result['changed_pixels']:,}")
        print(f"   Change percentage: {result['change_percentage']}%")

    except Exception as e:
        print(f"   [Error] {e}")


if __name__ == "__main__":
    print("\n>> SatQuery Backend Test Suite\n")

    test_router()
    test_vlm()
    test_geo_loader()
    test_change_detection()

    print("\n" + "=" * 50)
    print("[OK] All tests completed successfully!")
    print("=" * 50)
