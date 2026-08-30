"""
Automated Satellite Image Downloader using Wikimedia Commons & NASA public domain images
"""

import urllib.request
from pathlib import Path

# High quality stable satellite images from Wikimedia Commons / NASA
SAMPLES = {
    # Port of Los Angeles / Long Beach aerial/satellite view
    "urban_port.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Port_of_Los_Angeles_aerial_view.jpg/1280px-Port_of_Los_Angeles_aerial_view.jpg",
    # Aral Sea Before (2000)
    "lake_before.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Aral_Sea_1989_2014.jpg/800px-Aral_Sea_1989_2014.jpg",
    # Dubai Palm Jumeirah Satellite View
    "dubai_satellite.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Palm_Island_Dubai.jpg/1280px-Palm_Island_Dubai.jpg",
    # Agriculture / Crop Circles Satellite
    "agriculture.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Crop_circles_in_Kansas_-_Landsat_7.jpg/1280px-Crop_circles_in_Kansas_-_Landsat_7.jpg"
}

def download_samples():
    """Download real satellite datasets"""
    sample_dir = Path(__file__).parent / "sample_data"
    sample_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 60)
    print("Downloading Real Satellite Datasets")
    print("=" * 60)

    for filename, url in SAMPLES.items():
        dest = sample_dir / filename

        if dest.exists():
            print(f"[SKIP] {filename} already exists ({dest.stat().st_size / 1024:.1f} KB)")
            continue

        print(f"\n[DOWNLOADING] {filename}...")

        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'SatQueryBot/1.0 (Academic SIH Hackathon Project; contact@satquery.ai)'}
            )
            with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
                out_file.write(response.read())

            size_kb = dest.stat().st_size / 1024
            print(f"[OK] Saved {filename} ({size_kb:.1f} KB)")

        except Exception as e:
            print(f"[ERROR] Failed to download {filename}: {e}")

    print("\n" + "=" * 60)
    print("Download completed! Checking sample_data folder...")
    for f in sample_dir.glob("*.jpg"):
        print(f" - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    print("=" * 60)

if __name__ == "__main__":
    download_samples()
