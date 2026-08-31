"""
Change Detection with Red Highlighting
Compare any two images and get red-highlighted heatmap
"""

import sys
from pathlib import Path
from PIL import Image
from backend import detect_changes

if len(sys.argv) < 3:
    print("\nUsage:")
    print("  py compare.py <before_image> <after_image>")
    print("\nExample:")
    print("  py compare.py sample_data/flood_before.jpg sample_data/flood_after.jpg")
    print("  py compare.py my_image1.png my_image2.png")
    print()
    exit()

before_path = Path(sys.argv[1])
after_path = Path(sys.argv[2])

if not before_path.exists():
    print(f"[ERROR] Before image not found: {before_path}")
    exit()

if not after_path.exists():
    print(f"[ERROR] After image not found: {after_path}")
    exit()

print(f"\n[1/2] Loading images...")
print(f"  Before: {before_path.name}")
print(f"  After:  {after_path.name}")

img_before = Image.open(before_path)
img_after = Image.open(after_path)

print(f"\n[2/2] Running change detection...")
result = detect_changes(img_before, img_after)

# Save heatmap
output_name = f"change_{before_path.stem}_vs_{after_path.stem}.png"
result['diff_heatmap'].save(output_name)

print("\n" + "=" * 60)
print("CHANGE DETECTION RESULTS")
print("=" * 60)
print(f"Summary: {result['summary']}")
print(f"Changed Area: {result['change_percentage']}%")
print(f"Changed Pixels: {result['changed_pixels']:,} / {result['total_pixels']:,}")
print(f"\n[SAVED] Red heatmap: {output_name}")
print("=" * 60)
print(f"\nOpen '{output_name}' to see RED highlighting on changed areas!")
