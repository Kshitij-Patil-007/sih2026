"""
Generate Realistic-Looking Satellite Test Images
Creates synthetic satellite imagery for testing until real datasets are available
"""

from PIL import Image, ImageDraw
import numpy as np
import random

def create_urban_port_image():
    """Create a synthetic urban port scene"""
    img = Image.new('RGB', (1024, 1024))
    draw = ImageDraw.Draw(img)

    # Water (dark blue)
    draw.rectangle([0, 0, 1024, 400], fill=(30, 60, 110))

    # Port/harbor structures
    for i in range(8):
        x = 100 + i * 120
        draw.rectangle([x, 350, x+80, 450], fill=(140, 140, 140))

    # Ships
    for i in range(5):
        x = 150 + i * 180
        y = 200 + random.randint(-50, 50)
        draw.rectangle([x, y, x+60, y+120], fill=(180, 180, 180))

    # Urban area (buildings)
    for i in range(12):
        for j in range(8):
            x = 50 + i * 80
            y = 500 + j * 60
            draw.rectangle([x, y, x+60, y+40], fill=(100, 100, 100))

    # Roads
    draw.rectangle([0, 470, 1024, 485], fill=(80, 80, 80))
    draw.rectangle([400, 400, 415, 1024], fill=(80, 80, 80))

    return img

def create_flood_images():
    """Create before/after flood scenario"""
    base = Image.new('RGB', (800, 800))
    draw_before = ImageDraw.Draw(base)

    # Land (brown/green)
    draw_before.rectangle([0, 0, 800, 800], fill=(100, 120, 80))

    # River (narrow)
    draw_before.rectangle([300, 0, 350, 800], fill=(50, 100, 150))

    # Buildings
    for i in range(10):
        for j in range(10):
            x = 50 + i * 70
            y = 50 + j * 70
            if not (280 < x < 370):  # Not in river
                draw_before.rectangle([x, y, x+50, y+50], fill=(120, 120, 120))

    before = base.copy()

    # After: wider flooded area
    after = base.copy()
    draw_after = ImageDraw.Draw(after)
    draw_after.rectangle([200, 0, 450, 800], fill=(50, 100, 150))  # Wider flood

    return before, after

def create_deforestation_images():
    """Create before/after deforestation"""
    before = Image.new('RGB', (800, 800))
    draw_before = ImageDraw.Draw(before)

    # Dense forest (green)
    draw_before.rectangle([0, 0, 800, 800], fill=(60, 120, 60))

    # After: cleared areas (brown)
    after = before.copy()
    draw_after = ImageDraw.Draw(after)

    # Clearcut areas
    draw_after.rectangle([200, 200, 600, 400], fill=(140, 100, 70))
    draw_after.rectangle([100, 450, 400, 700], fill=(140, 100, 70))

    # Roads through forest
    draw_after.rectangle([0, 300, 800, 315], fill=(100, 100, 100))
    draw_after.rectangle([350, 0, 365, 800], fill=(100, 100, 100))

    return before, after

def generate_all_samples():
    """Generate all sample datasets"""
    print("\n" + "=" * 60)
    print("Generating Synthetic Satellite Test Images")
    print("=" * 60)

    sample_dir = Path(__file__).parent / "sample_data"
    sample_dir.mkdir(exist_ok=True)

    # Urban port
    print("\n[1/5] Creating urban_port.jpg...")
    urban = create_urban_port_image()
    urban.save(sample_dir / "urban_port.jpg", quality=95)
    print("   [OK] Saved urban_port.jpg")

    # Flood before/after
    print("\n[2/5] Creating flood_before.jpg...")
    print("[3/5] Creating flood_after.jpg...")
    flood_before, flood_after = create_flood_images()
    flood_before.save(sample_dir / "flood_before.jpg", quality=95)
    flood_after.save(sample_dir / "flood_after.jpg", quality=95)
    print("   [OK] Saved flood before/after pair")

    # Deforestation before/after
    print("\n[4/5] Creating deforest_before.jpg...")
    print("[5/5] Creating deforest_after.jpg...")
    deforest_before, deforest_after = create_deforestation_images()
    deforest_before.save(sample_dir / "deforest_before.jpg", quality=95)
    deforest_after.save(sample_dir / "deforest_after.jpg", quality=95)
    print("   [OK] Saved deforestation before/after pair")

    print("\n" + "=" * 60)
    print("Sample Generation Complete!")
    print("=" * 60)
    print("\nGenerated files:")
    for f in sample_dir.glob("*.jpg"):
        print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    print("\n[NOTE] These are synthetic test images.")
    print("For real satellite imagery, see sample_data/DOWNLOAD_SOURCES.md")

if __name__ == "__main__":
    from pathlib import Path
    generate_all_samples()
