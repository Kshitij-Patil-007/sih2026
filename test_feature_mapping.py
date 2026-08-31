"""
Test Feature Mapping - Roads Detection
"""
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Step 1: Upload image
print("Uploading test image...")
test_image = Path("test_satellite.png")

with open(test_image, "rb") as f:
    files = {"files": (test_image.name, f, "image/png")}
    response = requests.post(f"{BASE_URL}/upload", files=files)

data = response.json()
session_id = data['session_id']
print(f"Session ID: {session_id}")

# Step 2: Ask about roads
print("\nAsking: 'Highlight roads in this image'")
query_response = requests.post(
    f"{BASE_URL}/query",
    json={
        "session_id": session_id,
        "query_text": "Highlight roads in this image"
    }
)

result = query_response.json()
print(f"\nTask: {result['task']}")
print(f"Answer: {result['answer']}")
print(f"Confidence: {result.get('confidence')}")

if result.get('visual_evidence'):
    print(f"\nVisual Evidence:")
    print(f"  Type: {result['visual_evidence']['type']}")
    if 'path' in result['visual_evidence']:
        print(f"  Saved to: {result['visual_evidence']['path']}")
    if 'count' in result['visual_evidence']:
        print(f"  Feature count: {result['visual_evidence']['count']}")
    if 'coverage_pct' in result['visual_evidence']:
        print(f"  Coverage: {result['visual_evidence']['coverage_pct']}%")

print("\n[OK] Feature mapping test complete!")
