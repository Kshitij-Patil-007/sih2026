"""
Quick test to show red masking/highlighting in change detection
"""

from PIL import Image
from backend import detect_changes
from pathlib import Path

# Load flood before/after
sample_dir = Path("sample_data")
img_before = Image.open(sample_dir / "flood_before.jpg")
img_after = Image.open(sample_dir / "flood_after.jpg")

print("Running change detection with red highlighting...")
result = detect_changes(img_before, img_after)

# Save the heatmap
heatmap_path = "change_heatmap_demo.png"
result['diff_heatmap'].save(heatmap_path)

print(f"\n[OK] Red heatmap saved to: {heatmap_path}")
print(f"Changed area: {result['change_percentage']}%")
print(f"\nOpen '{heatmap_path}' to see RED highlighting on changed areas!")
