"""
Test All Sample Datasets with AI
Runs complete test suite on all generated sample satellite images
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from backend import process_query, detect_changes

load_dotenv()

def test_all_samples():
    sample_dir = Path(__file__).parent / "sample_data"

    print("\n" + "=" * 60)
    print("Testing SatQuery AI on All Sample Datasets")
    print("=" * 60)

    # 1. Single Image Analysis (Urban Port)
    print("\n[TEST 1] Single Image Analysis: urban_port.jpg")
    urban_img = Image.open(sample_dir / "urban_port.jpg")

    q1 = "Describe what you see in this satellite image. Identify water, port structures, and buildings."
    res1 = process_query(urban_img, q1, model_type="auto")

    print(f"Model: {res1['model_used']}")
    print(f"Answer:\n{res1['answer']}\n")

    # 2. Change Detection (Flood Disaster)
    print("\n" + "=" * 60)
    print("[TEST 2] Change Detection: Flood Disaster (Before vs After)")
    flood_before = Image.open(sample_dir / "flood_before.jpg")
    flood_after = Image.open(sample_dir / "flood_after.jpg")

    flood_diff = detect_changes(flood_before, flood_after)
    print(f"Summary: {flood_diff['summary']}")
    print(f"Change Percentage: {flood_diff['change_percentage']}%")
    print(f"Changed Pixels: {flood_diff['changed_pixels']:,}")

    # Ask AI to explain the disaster
    q2 = "This is a satellite change detection scenario. What happened to the river and surrounding land?"
    res2 = process_query(flood_after, q2, model_type="auto")
    print(f"\nAI Analysis of Post-Flood State:\n{res2['answer']}\n")

    # 3. Change Detection (Deforestation)
    print("\n" + "=" * 60)
    print("[TEST 3] Change Detection: Deforestation (Before vs After)")
    deforest_before = Image.open(sample_dir / "deforest_before.jpg")
    deforest_after = Image.open(sample_dir / "deforest_after.jpg")

    deforest_diff = detect_changes(deforest_before, deforest_after)
    print(f"Summary: {deforest_diff['summary']}")
    print(f"Change Percentage: {deforest_diff['change_percentage']}%")
    print(f"Changed Pixels: {deforest_diff['changed_pixels']:,}")

    print("\n" + "=" * 60)
    print("[ALL TESTS COMPLETED SUCCESSFULLY!]")
    print("=" * 60)

if __name__ == "__main__":
    test_all_samples()
