from __future__ import annotations

import base64
import io
import json
import os
import urllib.error
import urllib.request
from typing import Any

from PIL import Image

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
TIMEOUT_SEC = 18


class GeminiResult:
    def __init__(self, ok: bool, text: str, used_network: bool, error: str | None = None):
        self.ok = ok
        self.text = text
        self.used_network = used_network
        self.error = error


def _image_part(image: Image.Image) -> dict[str, Any]:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return {"inline_data": {"mime_type": "image/jpeg", "data": b64}}


def generate(prompt: str, images: list[Image.Image]) -> GeminiResult:
    """Call Gemini if a key is present. Offline / error → caller uses the local fallback."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return GeminiResult(False, "", False, "GEMINI_API_KEY not set — using local fallback.")

    # In 2026, Google changed API key format to AQ. prefix
    # Try the v1 endpoint (not v1beta) with updated authentication
    model = "gemini-1.5-flash-latest"

    # Try both v1 and v1beta endpoints
    urls_to_try = [
        f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}",
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
    ]

    parts: list[dict[str, Any]] = [{"text": prompt}]
    for image in images:
        parts.append(_image_part(image))

    body = json.dumps({"contents": [{"parts": parts}]}).encode("utf-8")

    last_error = None
    for url in urls_to_try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            text = (
                payload.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )
            if not text:
                last_error = "Gemini returned an empty candidate."
                continue
            return GeminiResult(True, text, True, None)
        except urllib.error.URLError as exc:
            last_error = f"Network/API error: {exc}"
            continue
        except Exception as exc:
            last_error = f"Gemini client error: {exc}"
            continue

    # If all attempts failed, return the last error
    return GeminiResult(False, "", True, last_error or "All endpoints failed")
