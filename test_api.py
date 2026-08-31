"""
Quick API Test Script
Tests the FastAPI backend endpoints without needing a frontend
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test if server is running"""
    print("=" * 60)
    print("Testing Health Check Endpoint")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✓ Server is online!")
        print(f"  Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running. Start it with: python main.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_upload_image():
    """Test image upload endpoint"""
    print("\n" + "=" * 60)
    print("Testing Image Upload")
    print("=" * 60)

    # Check if test image exists
    test_image = Path("test_satellite.png")
    if not test_image.exists():
        print("✗ test_satellite.png not found. Run test_integration.py first.")
        return None

    try:
        with open(test_image, "rb") as f:
            files = {"files": (test_image.name, f, "image/png")}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Image uploaded successfully!")
            print(f"  Session ID: {data['session_id']}")
            print(f"  Images: {len(data['images'])}")
            for img in data['images']:
                print(f"    - {img['modality']} image ({img['width']}x{img['height']})")
            return data['session_id']
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def test_query(session_id):
    """Test query endpoint"""
    print("\n" + "=" * 60)
    print("Testing Query Endpoint")
    print("=" * 60)

    if not session_id:
        print("✗ No session ID provided")
        return

    test_queries = [
        "What do you see in this satellite image?",
        "Describe the land cover types visible.",
        "Are there any buildings or urban structures?"
    ]

    for query in test_queries:
        print(f"\n  Query: {query}")
        try:
            payload = {
                "session_id": session_id,
                "query_text": query
            }
            response = requests.post(
                f"{BASE_URL}/query",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Task: {data['task']}")
                print(f"  ✓ Answer: {data['answer'][:100]}...")
                if data.get('confidence'):
                    print(f"  ✓ Confidence: {data['confidence']:.2f}")
            else:
                print(f"  ✗ Query failed: {response.status_code}")
                print(f"    {response.text}")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def main():
    print("\nSatQuery API Test Suite\n")

    # Test 1: Health check
    if not test_health_check():
        print("\n💡 Start the server first with:")
        print("   python main.py")
        return

    # Test 2: Upload image
    session_id = test_upload_image()

    # Test 3: Query
    if session_id:
        test_query(session_id)

    print("\n" + "=" * 60)
    print("API Testing Complete!")
    print("=" * 60)
    print("\nTo test manually in browser:")
    print(f"   Open: {BASE_URL}/docs")
    print("   (FastAPI auto-generated interactive API docs)")


if __name__ == "__main__":
    main()
