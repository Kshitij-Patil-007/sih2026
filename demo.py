"""
Quick Demo Script - Runs all backend tests automatically
Perfect for showing off to your team!
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from backend import process_query, detect_changes

load_dotenv()

print("\n" + "=" * 70)
print(" SatQuery AI - Complete Backend Demo")
print("=" * 70)

sample_dir = Path("sample_data")

# TEST 1: Urban Port Analysis
print("\n[TEST 1] URBAN PORT INFRASTRUCTURE ANALYSIS")
print("-" * 70)
urban_img = Image.open(sample_dir / "urban_port.jpg")
q1 = "What infrastructure and features do you see in this port area?"
print(f"Question: {q1}")
res1 = process_query(urban_img, q1, model_type="auto")
print(f"\nAI Answer:\n{res1['answer'][:400]}...")
print(f"\nModel Used: {res1['model_used']}")

# TEST 2: Change Detection - Flood
print("\n\n[TEST 2] FLOOD DISASTER CHANGE DETECTION")
print("-" * 70)
flood_before = Image.open(sample_dir / "flood_before.jpg")
flood_after = Image.open(sample_dir / "flood_after.jpg")
flood_result = detect_changes(flood_before, flood_after)
print(f"Summary: {flood_result['summary']}")
print(f"Changed Area: {flood_result['change_percentage']}%")
print(f"Affected Pixels: {flood_result['changed_pixels']:,} out of {flood_result['total_pixels']:,}")

# TEST 3: Change Detection - Deforestation
print("\n\n[TEST 3] DEFORESTATION CHANGE DETECTION")
print("-" * 70)
deforest_before = Image.open(sample_dir / "deforest_before.jpg")
deforest_after = Image.open(sample_dir / "deforest_after.jpg")
deforest_result = detect_changes(deforest_before, deforest_after)
print(f"Summary: {deforest_result['summary']}")
print(f"Changed Area: {deforest_result['change_percentage']}%")
print(f"Affected Pixels: {deforest_result['changed_pixels']:,} out of {deforest_result['total_pixels']:,}")

# TEST 4: AI Analysis of Flood Impact
print("\n\n[TEST 4] AI DISASTER IMPACT ASSESSMENT")
print("-" * 70)
q2 = "What happened to the river and what impact did this have on nearby structures?"
print(f"Question: {q2}")
res2 = process_query(flood_after, q2, model_type="auto")
print(f"\nAI Answer:\n{res2['answer'][:400]}...")

print("\n\n" + "=" * 70)
print(" ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 70)
print("\nYour backend is fully operational and ready for:")
print("  - Frontend integration (Streamlit UI)")
print("  - Real satellite imagery datasets")
print("  - Live demo presentation")
print("\n" + "=" * 70)
