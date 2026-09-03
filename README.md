# SatQuery AI - Multimodal Remote Sensing Assistant

**Smart India Hackathon 2026**

A prototype AI assistant for analyzing satellite imagery using natural language queries.

## 🏗️ Project Structure

```
sih2026/
├── backend/              # Backend logic (YOUR TEAM)
│   ├── __init__.py      # Main exports
│   ├── geo_loader.py    # GeoTIFF processing
│   ├── vlm_engine.py    # Vision-Language model integration
│   ├── change_detection.py  # Change detection algorithms
│   └── router.py        # Query classification
├── app.py               # Streamlit frontend (FRONTEND TEAM)
├── test_backend.py      # Backend test suite
├── requirements.txt     # Python dependencies
└── .env.example         # API key template
```

## 🚀 Quick Start

The core pipeline runs locally: feature mapping, land-cover VQA, change detection, and Optical + SAR fusion do not require Groq or any external API key.

### Backend

1. **Install dependencies:**
```bash
py -m pip install -r requirements.txt
```

2. **Start the FastAPI server:**
```bash
py -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The API docs are available at `http://localhost:8000/docs`.

### Frontend

In a second terminal:

```bash
cd satquery-frontend
npm install
npm run dev
```

Open the URL printed by Vite. The frontend defaults to `http://127.0.0.1:8000` for the API. To use another backend port, set `VITE_API_BASE` before starting Vite, for example:

```bash
VITE_API_BASE=http://127.0.0.1:8001 npm run dev
```

### Test the in-house feature mapper

```bash
py test_feature_mapping.py
``` 

The included sample images are in `sample_data/`; try `sample_data/city.png` with queries such as **Highlight all roads** or **Show all water bodies**.

### Optional API keys

Gemini and Claude are optional supplementary integrations. If they are not configured, the in-house models are used automatically. Copy `.env.example` only if you want to configure an optional integration.

### What Each Module Does

#### `backend/geo_loader.py`
- Loads GeoTIFF files
- Converts multi-band satellite images to RGB
- Handles image normalization and contrast stretching

#### `backend/vlm_engine.py`
- Connects to vision AI models (Gemini, Claude, or Hugging Face)
- Sends image + question, gets text answer
- Supports multiple model backends

#### `backend/change_detection.py`
- Compares two images pixel-by-pixel
- Generates heatmap showing differences
- Calculates NDVI for vegetation analysis

#### `backend/router.py`
- Classifies user queries
- Routes to appropriate backend module
- Extracts features user is asking about

## 📋 Your Day 1 Goals

- [ ] Run `test_backend.py` successfully
- [ ] Load a real GeoTIFF or satellite image
- [ ] Get a response from a vision model (even placeholder)
- [ ] Test change detection with 2 sample images

## 🎯 Integration Point with Frontend

The frontend will call:
```python
from backend import process_query, load_geotiff, detect_changes

# Single image Q&A
result = process_query(image, "What do you see?")

# Load satellite image
data = load_geotiff("path/to/satellite.tif")

# Compare two images
changes = detect_changes(image_before, image_after)
```

## 🔑 API Key Options

You need at least ONE of these:

1. **Google Gemini** (Free tier available)
   - Get key: https://makersuite.google.com/app/apikey
   - Add to `.env`: `GOOGLE_API_KEY=...`

2. **Anthropic Claude** (Free trial)
   - Get key: https://console.anthropic.com/
   - Add to `.env`: `ANTHROPIC_API_KEY=...`

3. **Hugging Face** (Free, but slower)
   - Models run locally, no API key required for most
   - Optional token for gated models

## 🧪 Testing

```bash
# Test all backend modules
py test_backend.py

# Test individual modules
py -c "from backend.router import route_query; print(route_query('What changed?'))"
```

## 📦 Next Steps After Day 1

- Replace placeholder responses with real vision model
- Test with actual satellite imagery datasets
- Optimize image preprocessing pipeline
- Add error handling and validation

## 🆘 Troubleshooting

**Import errors?**
```bash
py -m pip install --upgrade -r requirements.txt
```

**Can't load GeoTIFF?**
- Make sure `rasterio` is installed
- Falls back to PIL for regular images automatically

**Vision model not working?**
- Start with placeholder mode first
- Test API keys separately before integrating

---

Built for SIH 2026 | Team: [Your Team Name]
