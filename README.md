# SatQuery AI

**Smart India Hackathon 2026 · Multimodal remote-sensing assistant**

SatQuery accepts one or two satellite images and a natural-language question. Its FastAPI backend routes the request to an offline-first remote-sensing pipeline and returns an answer, confidence score, audit trail, and generated visual evidence.

## Current capabilities

- Single-image land-cover visual Q&A for optical or SAR imagery
- Feature mapping for roads, water, vegetation, buildings, and vehicles
- Bi-temporal change detection with a heatmap and hotspot regions
- Optical + SAR fusion for an aligned two-image pair
- PNG, JPEG, and GeoTIFF uploads
- SQLite-backed sessions and auditable model/preprocessing events
- Optional Gemini assistance for optical imagery; the local pipeline remains the fallback

The included models are hackathon-scale, CPU-friendly remote-sensing heuristics and stand-ins, not production-certified measurements. Results should be reviewed by a remote-sensing specialist.

## Repository layout

```text
sih2026/
├── backend/                    # Image processing, routing, models, database, audit trail
├── main.py                    # FastAPI application and REST endpoints
├── satquery-frontend/         # Canonical Vite frontend
├── sample_data/               # Demo inputs and source notes
├── test_backend.py            # Manual backend smoke script
├── test_feature_mapping.py    # Feature-mapper checks
├── requirements.txt           # Python dependencies
└── .env.example               # Optional local configuration template
```

## Quick start

### 1. Backend

Use Python 3.11+ (Python 3.12 is recommended) and run these commands from the repository root.

**Windows PowerShell:**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**macOS/Linux:**

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Check that `http://127.0.0.1:8000/health` returns an online status. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

### 2. Frontend

Open a second terminal and run:

```bash
cd satquery-frontend
npm ci
npm run dev
```

Open the local URL printed by Vite. The client defaults to `http://127.0.0.1:8000`. To use another backend, create `satquery-frontend/.env.local`:

```text
VITE_API_BASE=http://127.0.0.1:8001
```

Do not commit `.env.local`, API keys, `node_modules`, or build output.

### 3. Try the included samples

In the UI, select **Single Image** and upload `sample_data/city.png` or `sample_data/town.jpg`. Useful questions include:

- `Highlight all roads`
- `Show all water bodies`
- `Describe the land cover in this image`

For change detection, select **Bi-temporal Pair** and upload `sample_data/before.png` followed by `sample_data/after.png`, then ask `What changed between these images?`. For fusion, select **Optical + SAR Pair** and tag the two inputs explicitly.

## API contract

1. `POST /upload` — multipart form with one or two `files`; optional `modality_hints` JSON array (`optical`, `sar`, or `auto`). Returns a `session_id` and image metadata.
2. `POST /query` — JSON body `{ "session_id": "...", "query_text": "..." }`. Returns `task`, `answer`, `confidence`, `visual_evidence`, and `audit_trail`.
3. `GET /result/{query_id}` — retrieves a stored result and formatted audit trail.
4. `GET /report/{query_id}` — currently returns a JSON report payload; PDF generation is not enabled yet.
5. `GET /uploads/{session_id}/{filename}` — serves generated evidence images for the active local session.
6. `GET /health` — liveness check.

Relative evidence URLs in `visual_evidence.url` are resolved against the backend origin automatically by the frontend.

## Configuration and model behavior

Copy `.env.example` to `.env` only when enabling optional integrations. No API key is needed for the local feature mapper, change detector, fusion path, or local land-cover head. Gemini is attempted only for optical supplementary explanations and falls back to the local answer when unavailable. External API tests are manual and are not part of the offline smoke path.

## Testing

```bash
# Compile all backend modules
python -m compileall -q backend main.py

# Manual offline module smoke test
python test_backend.py

# Feature checks (uses test_satellite.png when present)
python -m pytest -q test_feature_mapping.py

# Frontend production build
cd satquery-frontend
npm ci
npm run build
```

The repository also contains legacy/manual scripts named `test_*_direct.py` and `test_groq*.py`; they may require credentials or network access and should not be used as the default offline check. `test_samples.py` refers to optional external sample names and is not part of the required smoke path.

## GitHub Pages deployment

The workflow in `satquery-frontend/.github/workflows/deploy.yml` builds from `satquery-frontend/` and publishes `satquery-frontend/dist`. GitHub Pages can host the static UI, but a browser on Pages cannot reach a teammate's `127.0.0.1` backend. For a connected public deployment, build with a reachable HTTPS `VITE_API_BASE` and configure the backend's CORS policy for that Pages origin. Local development is the supported end-to-end demo path.

## Known limitations

- CPU image processing can take time on large uploads; images are resized for inference.
- Change detection uses resize-based co-registration rather than a geospatial registration model.
- Feature masks are algorithmic approximations and can produce false positives.
- `/report/{query_id}` is JSON for now, despite the historical ReportLab dependency.
- Uploaded images, generated evidence, and the SQLite database are local runtime state and are intentionally ignored by Git.

Built for SIH 2026.
