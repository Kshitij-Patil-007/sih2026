"""
Direct test of Gemini API to diagnose 401 error
"""
import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')
print(f"API Key present: {'Yes' if api_key else 'No'}")
print(f"Key format: {api_key[:10]}..." if api_key else "No key")

if not api_key:
    print("ERROR: No API key found in .env")
    exit(1)

# Try different endpoints
endpoints = [
    "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
    "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent",
]

body = json.dumps({
    "contents": [{
        "parts": [{"text": "Say hello"}]
    }]
}).encode('utf-8')

for endpoint in endpoints:
    url = f"{endpoint}?key={api_key}"
    print(f"\n\nTrying: {endpoint}")

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"SUCCESS!")
            print(f"Response: {json.dumps(result, indent=2)[:200]}...")
            break
    except urllib.error.HTTPError as e:
        print(f"FAIL - HTTP {e.code}: {e.reason}")
        error_body = e.read().decode('utf-8')
        print(f"Error details: {error_body[:500]}")
    except Exception as e:
        print(f"FAIL - Error: {e}")
