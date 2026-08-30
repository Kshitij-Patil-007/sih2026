"""
Ask AI about ANY image
Usage:
    py ask.py <path_to_image> "<your_question>"

Example:
    py ask.py sample_data/urban_port.jpg "How many ships are docked?"
    py ask.py my_screenshot.png "What changes do you see?"
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from backend import process_query, load_geotiff

load_dotenv()

def main():
    if len(sys.argv) < 3:
        print("\n" + "=" * 60)
        print("SatQuery AI - Ask Anything About Any Image")
        print("=" * 60)
        print("Usage:")
        print('    py ask.py <image_path> "<your_question>"')
        print("\nExamples:")
        print('    py ask.py sample_data/urban_port.jpg "Describe what you see"')
        print('    py ask.py sample_data/flood_after.jpg "Is there flood damage?"')
        print('    py ask.py C:/Users/Kshitij/Desktop/mysatellite.png "Count the tanks"')
        print("=" * 60 + "\n")
        return

    image_path = sys.argv[1]
    question = sys.argv[2]

    path = Path(image_path)
    if not path.exists():
        print(f"[ERROR] File not found: {image_path}")
        return

    print(f"\n[1/2] Loading image: {path.name}...")
    try:
        # Load using our smart loader (handles TIFF, PNG, JPG)
        data = load_geotiff(path)
        img = data['image']
        print(f"      Image size: {img.width}x{img.height} pixels")
    except Exception as e:
        print(f"[ERROR] Failed to load image: {e}")
        return

    print(f"\n[2/2] Asking AI: \"{question}\"...")
    try:
        result = process_query(img, question, model_type="auto")

        print("\n" + "=" * 65)
        print("AI ANALYSIS")
        print("=" * 65)
        print(f"Image:    {path.name}")
        print(f"Model:    {result['model_used']}")
        print(f"Question: {question}")
        print("-" * 65)
        print(result['answer'])
        print("=" * 65 + "\n")

    except Exception as e:
        print(f"[ERROR] AI processing failed: {e}")

if __name__ == "__main__":
    main()
