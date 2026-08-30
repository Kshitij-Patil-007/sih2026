"""
Quick test to verify Gemini API is working with images
"""

import os
from dotenv import load_dotenv
from backend.vlm_engine import process_query
from PIL import Image
import numpy as np

# Load API key from .env
load_dotenv()

def test_gemini_api():
    """Test Gemini with a generated satellite-like image"""
    print("\n" + "=" * 60)
    print("Testing Gemini Vision API")
    print("=" * 60)

    # Check if API key is loaded
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\n[ERROR] API key not found in .env file!")
        print("Please edit .env and add your actual Gemini API key.")
        return

    print(f"\n[OK] API Key loaded: {api_key[:20]}...")

    # Create a test image (simulating satellite imagery)
    print("\n[Test] Creating test image...")
    test_image = Image.fromarray(
        np.random.randint(50, 200, (512, 512, 3), dtype=np.uint8)
    )

    # Test with Gemini
    print("\n[Test] Calling Gemini API...")
    try:
        result = process_query(
            test_image,
            "Describe what you see in this image. Is it a satellite image?",
            model_type="gemini"
        )

        print(f"\n[SUCCESS] Gemini responded!")
        print(f"Model: {result['model_used']}")
        print(f"Question: {result['query']}")
        print(f"\nAnswer:\n{result['answer']}")

        print("\n" + "=" * 60)
        print("[OK] Gemini API is working! Ready for real satellite images.")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Gemini API call failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API key is correct in .env")
        print("2. Make sure you have internet connection")
        print("3. Verify API key has proper permissions at https://makersuite.google.com/")

if __name__ == "__main__":
    test_gemini_api()
