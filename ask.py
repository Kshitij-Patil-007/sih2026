"""
Ask AI about ANY image — now with feature mapping!
Usage:
    py ask.py <path_to_image> "<your_question>"

Example:
    py ask.py sample_data/urban_port.jpg "How many ships are docked?"
    py ask.py sample_data/op-1-fcc.png "How many water bodies are there?"
    py ask.py sample_data/op-1-fcc.png "Highlight the vegetation"
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from backend import process_query, load_geotiff, detect_and_highlight
from backend.router import route_query, extract_features
from backend.feature_mapper import _extract_feature_from_query

load_dotenv()

# Keywords that trigger the feature mapper (highlight/count mode)
MAPPING_KEYWORDS = [
    'highlight', 'show me', 'show', 'map', 'mark', 'outline',
    'how many', 'count', 'detect', 'find', 'locate', 'identify',
    'where are', 'where is', 'segment', 'isolate'
]

# Feature color mapping for different features
FEATURE_COLORS = {
    'water':        (30, 100, 255),   # Blue
    'buildings':    (220, 30, 30),    # Red
    'roads':        (255, 165, 0),    # Orange
    'vegetation':   (30, 200, 30),    # Green
    'vehicles':     (255, 255, 0),    # Yellow
    'agricultural': (180, 120, 40),   # Brown
    'features':     (220, 30, 30),    # Red (default)
}


def _needs_mapping(question: str) -> bool:
    """Check if the query needs visual mapping (highlight/count features)"""
    q = question.lower()
    return any(kw in q for kw in MAPPING_KEYWORDS)


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
        print()
        print("  MAPPING (auto-highlights features):")
        print('    py ask.py sample_data/op-1-fcc.png "How many water bodies?"')
        print('    py ask.py sample_data/op-1-fcc.png "Highlight the vegetation"')
        print('    py ask.py sample_data/op-1-fcc.png "Detect buildings"')
        print('    py ask.py sample_data/op-1-fcc.png "Find roads in this image"')
        print("=" * 60 + "\n")
        return

    image_path = sys.argv[1]
    question = sys.argv[2]

    path = Path(image_path)
    if not path.exists():
        print(f"[ERROR] File not found: {image_path}")
        return

    print(f"\n[1/3] Loading image: {path.name}...")
    try:
        data = load_geotiff(path)
        img = data['image']
        print(f"      Image size: {img.width}x{img.height} pixels")
    except Exception as e:
        print(f"[ERROR] Failed to load image: {e}")
        return

    # Decide: mapping mode or plain AI Q&A
    if _needs_mapping(question):
        _run_mapping(img, question, path)
    else:
        _run_qa(img, question, path)


def _run_mapping(img, question, path):
    """Feature mapping mode — detect, highlight, count"""
    feature = _extract_feature_from_query(question)
    color = FEATURE_COLORS.get(feature, (220, 30, 30))

    print(f"[2/3] Detecting '{feature}' in the image...")
    result = detect_and_highlight(img, question, highlight_color=color)

    # Save highlighted image
    output_name = f"{path.stem}_mapped_{feature}.png"
    output_path = path.parent / output_name
    result['highlighted'].save(output_path)

    print(f"[3/3] Analysis complete!")
    print("\n" + "=" * 65)
    print("FEATURE MAPPING RESULT")
    print("=" * 65)
    print(f"Image:     {path.name}")
    print(f"Feature:   {feature}")
    print(f"Count:     {result['count']} region(s)")
    print(f"Coverage:  {result['coverage_pct']}%")
    print("-" * 65)
    print(result['answer'])
    print("-" * 65)

    if result['regions']:
        print("\nRegion Details:")
        for r in result['regions'][:10]:  # Show top 10
            print(f"  #{r['id']:>3}  |  {r['area_pixels']:>8,} px  |  center: ({r['centroid_xy'][0]}, {r['centroid_xy'][1]})")

    print(f"\nHighlighted image saved: {output_path}")
    print("=" * 65 + "\n")

    # Also pass to AI for a richer natural language description
    try:
        print("[BONUS] Getting AI description...")
        ai_prompt = (
            f"This satellite image has {result['count']} detected {feature} regions "
            f"covering {result['coverage_pct']}% of the image. "
            f"Based on the image, describe these {feature} features in detail. "
            f"Original question: {question}"
        )
        ai_result = process_query(img, ai_prompt, model_type="auto")
        print(f"\nAI Analysis ({ai_result['model_used']}):")
        print("-" * 65)
        print(ai_result['answer'])
        print("=" * 65 + "\n")
    except Exception:
        pass  # AI description is optional


def _run_qa(img, question, path):
    """Plain AI Q&A mode"""
    print(f"\n[2/3] Asking AI: \"{question}\"...")
    try:
        result = process_query(img, question, model_type="auto")

        print(f"[3/3] Response received!")
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
