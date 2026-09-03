"""
Gemini API client using OAuth2 authentication.

Google's newer Gemini credentials require OAuth2 Bearer tokens instead of
legacy API-key-only requests. This module caches and refreshes OAuth tokens,
then calls generateContent with the same simple interface used by vlm_engine.
"""
from __future__ import annotations

import base64
import io
import json
import os
import pickle
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from PIL import Image

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
TIMEOUT_SEC = int(os.environ.get("GEMINI_TIMEOUT_SEC", "45"))
SCOPES = ["https://www.googleapis.com/auth/generative-language.retriever"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = PROJECT_ROOT / "token.pickle"
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"


class GeminiResult:
    def __init__(self, ok: bool, text: str, used_network: bool, error: str | None = None):
        self.ok = ok
        self.text = text
        self.used_network = used_network
        self.error = error


def _get_oauth_token() -> str | None:
    creds = None

    if TOKEN_PATH.exists():
        with TOKEN_PATH.open("rb") as token_file:
            creds = pickle.load(token_file)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as exc:  # noqa: BLE001 - surface as offline fallback
                print(f"Gemini token refresh failed: {exc}")
                creds = None

        if not creds:
            if not CREDENTIALS_PATH.exists():
                print(f"Gemini OAuth credentials file missing: {CREDENTIALS_PATH}")
                return None

            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
                creds = flow.run_local_server(port=8080)
            except Exception as exc:  # noqa: BLE001 - surface as offline fallback
                print(f"Gemini OAuth flow failed: {exc}")
                return None

        with TOKEN_PATH.open("wb") as token_file:
            pickle.dump(creds, token_file)

    return creds.token if creds else None


def _image_part(image: Image.Image) -> dict[str, Any]:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return {"inline_data": {"mime_type": "image/jpeg", "data": b64}}


def generate(prompt: str, images: list[Image.Image]) -> GeminiResult:
    access_token = _get_oauth_token()

    if access_token:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
    else:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return GeminiResult(False, "", False, "No Gemini OAuth token or API key available.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

    parts: list[dict[str, Any]] = [{"text": prompt}]
    parts.extend(_image_part(image) for image in images)

    body = json.dumps(
        {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.35,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 2048,
            },
        }
    ).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers)
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
            return GeminiResult(False, "", True, "Gemini returned an empty candidate.")
        return GeminiResult(True, text, True, None)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return GeminiResult(False, "", True, f"HTTP {exc.code}: {exc.reason}. {error_body[:400]}")
    except urllib.error.URLError as exc:
        return GeminiResult(False, "", True, f"Network error: {exc}")
    except Exception as exc:  # noqa: BLE001 - caller falls back cleanly
        return GeminiResult(False, "", True, f"Gemini client error: {exc}")


def check_auth_status() -> dict[str, Any]:
    status = {
        "oauth_available": False,
        "api_key_available": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
        "credentials_file_exists": CREDENTIALS_PATH.exists(),
        "token_file_exists": TOKEN_PATH.exists(),
        "method": None,
        "error": None,
    }

    if TOKEN_PATH.exists():
        try:
            with TOKEN_PATH.open("rb") as token_file:
                creds = pickle.load(token_file)
            if creds and creds.valid:
                status["oauth_available"] = True
                status["method"] = "oauth2"
        except Exception as exc:  # noqa: BLE001
            status["error"] = f"Token file could not be read: {exc}"

    if not status["method"] and status["api_key_available"]:
        status["method"] = "api_key"

    return status
