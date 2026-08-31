"""
Simple API Test Script - No special characters
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
        print("[OK] Server is online!")
        print(f"  Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server is not running. Start it with: python main.py")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_upload_image():
    """Test image upload endpoint"""
    print("\n" + "=" * 60)
    print("Testing Image Upload")
    print("=" * 60)

    test_image = Path("test_satellite.png")
    if not test_image.exists():
        print("[ERROR] test_satellite.png not found. Run test_integration.py first.")
        return None

    try:
        with open(test_image, "rb") as f:
            files = {"files": (test_image.name, f, "image/png")}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("[OK] Image uploaded successfully!")
            print(f"  Session ID: {data['session_id']}")
            print(f"  Images: {len(data['images'])}")
            for img in data['images']:
                print(f"    - {img['modality']} image ({img['width']}x{img['height']})")
            return data['session_id']
        else:
            print(f"[ERROR] Upload failed: {response.status_code}")
            print(f"  {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def test_query(session_id):
    """Test query endpoint"""
    print("\n" + "=" * 60)
    print("Testing Query Endpoint")
    print("=" * 60)

    if not session_id:
        print("[ERROR] No session ID provided")
        return

    test_queries = [
        "What do you see in this satellite image?",
        "Describe the land cover types visible.",
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
                print(f"  [OK] Task: {data['task']}")
                print(f"  [OK] Answer: {data['answer'][:100]}...")
                if data.get('confidence'):
                    print(f"  [OK] Confidence: {data['confidence']:.2f}")
            else:
                print(f"  [ERROR] Query failed: {response.status_code}")
                print(f"    {response.text}")
        except Exception as e:
            print(f"  [ERROR] {e}")


def main():
    print("\nSatQuery API Test Suite\n")

    # Test 1: Health check
    if not test_health_check():
        print("\nStart the server first with:")
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
    print("\nTo test interactively in browser:")
    print(f"   Open: {BASE_URL}/docs")
    print("   (FastAPI auto-generated interactive API documentation)")


if __name__ == "__main__":
    main()
