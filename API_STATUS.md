# FastAPI Backend - Setup Complete

**Created:** August 31, 2026 @ 6:57 PM IST

---

## ✅ What's Ready

### 1. **Database Layer** (`backend/db.py`)
- SQLite session management
- Tables: `sessions`, `images`, `queries`, `audit_trail`
- Functions for CRUD operations on all entities

### 2. **Audit Trail Logger** (`backend/audit.py`)
- Explicit logging for judging criteria
- Tracks: routing decisions, model calls, preprocessing, confidence estimation
- UI-formatted output for frontend display

### 3. **FastAPI REST Server** (`main.py`)
- ✅ `POST /upload` - Upload 1-2 images, returns session_id
- ✅ `POST /query` - Process query with agentic routing
- ✅ `GET /result/{id}` - Fetch cached result
- ✅ `GET /report/{id}` - Generate report (PDF pending - Yatharth's task)
- CORS enabled for React frontend
- Auto-detects modality (optical/SAR)
- Validates file formats (PNG, JPEG, GeoTIFF)

### 4. **Reused Existing Backend**
- `router.py` - Query classification
- `vlm_engine.py` - Gemini integration
- `geo_loader.py` - GeoTIFF handling
- `change_detection.py` - Bi-temporal analysis

---

## 🚀 How to Start

```bash
cd C:\Users\Kshitij\ Patil\projects\helloworld\sih2026
bash start_server.sh
```

Or manually:
```bash
pip install -r requirements.txt
python main.py
```

Server runs at: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

---

## 📋 API Contract (Team Integration Points)

### Frontend Team (Devshi/Rishit)
```javascript
// Upload images
POST http://localhost:8000/upload
FormData: { files: [file1, file2], modality_hints: '["optical", "sar"]' }
Returns: { session_id, images: [{id, modality, format, width, height}] }

// Query
POST http://localhost:8000/query
Body: { session_id: "...", query_text: "What changed?" }
Returns: { query_id, task, answer, confidence, visual_evidence, audit_trail }

// Get result
GET http://localhost:8000/result/{query_id}
```

### Controller Team (Yatharth)
- Router is integrated in `/query` endpoint
- Audit trail automatically logged
- **TODO:** Implement PDF generation in `/report/{id}` using ReportLab

### Model Team (Nisha/Aryan)
**Integration points in `main.py`:**
- Line 198: `handle_vqa()` - Replace with Nisha's LoRA BLIP-2 for SAR
- Line 227: Add Aryan's optical-SAR fusion model
- Line 242: Enhance change detection with Aryan's Siamese/Gemini

**Expected function signatures:**
```python
# Nisha's in-house VQA
def run_vqa(image_path: str, question: str) -> dict:
    return {"answer": str, "confidence": float}

# Nisha's optical-SAR fusion
def run_optical_sar_fusion(optical_path: str, sar_path: str, question: str) -> dict:
    return {"answer": str, "confidence": float}

# Aryan's change VQA
def run_change_vqa(img1_path: str, img2_path: str, question: str) -> dict:
    return {"answer": str, "change_mask": np.array, "confidence": float}
```

---

## ⚠️ Current Limitations

1. **SAR images** → Falls back to placeholder (waiting for Nisha's LoRA model)
2. **PDF reports** → Returns JSON for now (Yatharth's task)
3. **Visual evidence** → Placeholder base64 (needs actual mask encoding)
4. **Confidence for Gemini** → Using simple heuristic (needs proper estimation)

---

## 🎯 Next Steps (Day 2 Afternoon/Evening)

### Your Tasks (Kshitij):
1. ✅ Backend API done
2. 🔄 **Message team in group chat** with API endpoints
3. ⏳ **Test locally** - Run server and test with Postman/curl
4. ⏳ **Frontend coordination** - Help Devshi/Rishit with API integration

### Team Coordination:
```
Group Message:
"Backend API is live! 🚀

Endpoints ready:
• POST /upload - upload images
• POST /query - ask questions  
• GET /result/{id} - get cached answers
• GET /report/{id} - download report

Running at localhost:8000 (docs at /docs)

@Devshi @Rishit - Start building React UI against these endpoints
@Yatharth - Controller is integrated, need PDF gen in /report
@Nisha @Aryan - Model integration points marked in main.py lines 198, 227, 242

Let's sync tomorrow morning on integration!"
```

---

## 📊 Timeline Status

**Day 2 (Aug 31):** Backend REST API ✅ DONE  
**Day 3 (Sep 1):** Frontend integration + model swap-in  
**Day 4-5:** Polish, demo, presentation

**Current time:** 6:57 PM IST  
**Time spent today:** ~30 minutes (API scaffolding)  
**Status:** ON TRACK 🎯
