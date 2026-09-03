"""
Quick test script for Groq Vision API
Tests the VLM engine with your satellite images
"""

import os
import sys
from pathlib import Path
from PIL import Image

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from vlm_engine import process_query

def test_groq():
    """Test Groq with a satellite image"""

    # Check for API key
    if not os.environ.get("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not found in environment!")
        print("Please add it to your .env file or set it:")
        print("  export GROQ_API_KEY=gsk_your_key_here")
        return

    print("✅ GROQ_API_KEY found")
    print("\n" + "="*60)

    # Find a test image
    sample_dirs = [
        Path("samples"),
        Path("data/samples"),
        Path("../samples"),
    ]

    test_image = None
    for dir in sample_dirs:
        if dir.exists():
            images = list(dir.glob("*.tif")) + list(dir.glob("*.png")) + list(dir.glob("*.jpg"))
            if images:
                test_image = images[0]
                break

    if not test_image:
        print("⚠️  No test images found in samples/")
        print("Please provide an image path:")
        img_path = input("Image path: ").strip()
        if img_path:
            test_image = Path(img_path)

    if not test_image or not test_image.exists():
        print("❌ No valid image found. Exiting.")
        return

    print(f"📷 Testing with: {test_image}")

    # Load image
    try:
        image = Image.open(test_image)
        print(f"✅ Image loaded: {image.size[0]}x{image.size[1]}")
    except Exception as e:
        print(f"❌ Failed to load image: {e}")
        return

    # Test query
    test_questions = [
        "What do you see in this satellite image?",
        "Describe the urban planning and infrastructure visible in this area.",
        "Identify any roads, buildings, or green spaces."
    ]

    print("\n" + "="*60)
    print("🚀 Testing Groq API with Llama 3.2 Vision 90B")
    print("="*60 + "\n")

    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 60)

        try:
            result = process_query(image, question, model_type="groq")

            print(f"✅ Model: {result['model_used']}")
            print(f"📊 Image size: {result['image_size']}")
            print(f"\n💬 Answer:\n{result['answer']}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print("-" * 60)

        if i < len(test_questions):
            input("\nPress Enter for next question...")

    print("\n" + "="*60)
    print("✅ Test complete!")
    print("="*60)

if __name__ == "__main__":
    # Load .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed, using existing env vars")

    test_groq()
