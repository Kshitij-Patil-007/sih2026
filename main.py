"""
FastAPI Main Server
Provides REST API for satellite image Q&A with agentic routing
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import shutil
from PIL import Image
import os

# Import backend modules
from backend import db, audit
from backend.router import route_query
from backend.geo_loader import load_geotiff
from backend.vlm_engine import ask_vision_model
from backend.change_detection import detect_changes
from backend.feature_mapper import detect_and_highlight

app = FastAPI(title="SatQuery AI API", version="1.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Pydantic models
class QueryRequest(BaseModel):
    session_id: str
    query_text: str

class ImageMetadata(BaseModel):
    id: str
    modality: Optional[str]
    format: str
    width: int
    height: int

class UploadResponse(BaseModel):
    session_id: str
    images: List[ImageMetadata]

class VisualEvidence(BaseModel):
    type: str  # "feature_mask", "change_mask", "bbox", etc.
    data: Optional[str] = None  # base64 or URL
    url: Optional[str] = None  # URL to highlighted image
    count: Optional[int] = None
    coverage_pct: Optional[float] = None

class AuditTrail(BaseModel):
    task: str
    models_used: List[str]
    parameters: dict
    routing_decision: Optional[str] = None
    preprocessing_steps: Optional[List[str]] = None

class QueryResponse(BaseModel):
    task: str
    answer: str
    confidence: Optional[float]
    visual_evidence: Optional[VisualEvidence]
    audit_trail: AuditTrail


HTML_FILE = Path(__file__).parent / "test_upload.html"

@app.get("/")
def root():
    """Serve the Web UI test interface"""
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE)
    return {"status": "online", "service": "SatQuery AI"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "online", "service": "SatQuery AI"}


@app.post("/upload", response_model=UploadResponse)
async def upload_images(
    files: List[UploadFile] = File(..., description="Select 1-2 satellite images (PNG, JPEG, or GeoTIFF)"),
    modality_hints: Optional[str] = Form(None, description='Optional JSON array like ["optical", "sar"]')
):
    """
    Upload 1-2 satellite images
    Returns session_id for subsequent queries

    **Note:** Swagger UI doesn't handle multiple file uploads well.
    **Use the test page instead:** Open `test_upload.html` in your browser for the best experience.

    **Accepted formats:** PNG, JPEG, GeoTIFF (.tif, .tiff)
    """
    if len(files) < 1 or len(files) > 2:
        raise HTTPException(status_code=400, detail="Must upload 1 or 2 images")

    # Validate file formats
    valid_formats = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {file.filename}. Allowed: PNG, JPEG, GeoTIFF"
            )

    # Create session
    session_id = db.create_session(len(files))
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    # Process modality hints if provided
    import json
    modality_list = json.loads(modality_hints) if modality_hints else [None] * len(files)

    images_metadata = []

    for idx, (file, modality) in enumerate(zip(files, modality_list)):
        # Save file
        filepath = session_dir / file.filename
        with filepath.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get image dimensions
        try:
            if filepath.suffix.lower() in [".tif", ".tiff"]:
                # GeoTIFF - load with backend
                geo_data = load_geotiff(str(filepath))
                img = geo_data["image"]
            else:
                img = Image.open(filepath)

            width, height = img.size
            format_type = filepath.suffix.lower().replace(".", "")

            # Auto-detect modality if not provided
            if not modality or modality == "auto":
                # Simple heuristic: grayscale often = SAR
                if img.mode == "L" or (hasattr(img, "getbands") and len(img.getbands()) == 1):
                    modality = "sar"
                else:
                    modality = "optical"

            # Store in database
            image_id = db.add_image(
                session_id=session_id,
                filename=file.filename,
                filepath=str(filepath),
                modality=modality,
                format=format_type,
                width=width,
                height=height
            )

            images_metadata.append(ImageMetadata(
                id=image_id,
                modality=modality,
                format=format_type,
                width=width,
                height=height
            ))

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process {file.filename}: {str(e)}")

    return UploadResponse(session_id=session_id, images=images_metadata)


@app.post("/upload-simple")
async def upload_simple(
    file: UploadFile = File(..., description="Single satellite image for testing in Swagger UI")
):
    """
    **Simplified upload endpoint for testing in Swagger UI**

    Upload a single satellite image and get a session_id.
    This endpoint works better in Swagger UI than the multi-file /upload endpoint.

    For production use with 1-2 images, use /upload or the test_upload.html page.
    """
    # Validate file format
    valid_formats = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    ext = Path(file.filename).suffix.lower()
    if ext not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {file.filename}. Allowed: PNG, JPEG, GeoTIFF"
        )

    # Create session
    session_id = db.create_session(1)
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    # Save file
    filepath = session_dir / file.filename
    with filepath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get image dimensions
    try:
        if filepath.suffix.lower() in [".tif", ".tiff"]:
            geo_data = load_geotiff(str(filepath))
            img = geo_data["image"]
        else:
            img = Image.open(filepath)

        width, height = img.size
        format_type = filepath.suffix.lower().replace(".", "")

        # Auto-detect modality
        if img.mode == "L" or (hasattr(img, "getbands") and len(img.getbands()) == 1):
            modality = "sar"
        else:
            modality = "optical"

        # Store in database
        image_id = db.add_image(
            session_id=session_id,
            filename=file.filename,
            filepath=str(filepath),
            modality=modality,
            format=format_type,
            width=width,
            height=height
        )

        return {
            "session_id": session_id,
            "image": {
                "id": image_id,
                "modality": modality,
                "format": format_type,
                "width": width,
                "height": height,
                "preview_url": f"/uploads/{session_id}/{file.filename}"
            },
            "note": "Use this session_id with /query endpoint"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process {file.filename}: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query against uploaded images
    Routes to appropriate model and returns answer + audit trail
    """
    # Validate session
    if not db.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Get images
    images = db.get_session_images(request.session_id)
    if not images:
        raise HTTPException(status_code=400, detail="No images in session")

    # Route query
    routing_result = route_query(request.query_text)
    task_type = routing_result["query_type"]

    # Create query record
    query_id = db.create_query(request.session_id, request.query_text, task_type)

    # Log routing decision
    audit.log_routing_decision(
        query_id=query_id,
        query_text=request.query_text,
        task=task_type,
        image_count=len(images),
        modalities=[img["modality"] for img in images],
        reasoning=routing_result["suggested_action"]
    )

    try:
        # Execute based on task type
        if task_type == "change_detection" and len(images) == 2:
            result = await handle_change_detection(query_id, images, request.query_text)

        elif task_type == "feature_mapping":
            result = await handle_feature_mapping(query_id, images[0], request.query_text)

        elif task_type in ["single_image", "ndvi_analysis"]:
            result = await handle_vqa(query_id, images[0], request.query_text)

        else:
            raise HTTPException(status_code=400, detail=f"Incompatible query type '{task_type}' for {len(images)} image(s)")

        # Store result
        db.update_query_result(
            query_id=query_id,
            answer=result["answer"],
            confidence=result.get("confidence"),
            visual_evidence=result.get("visual_evidence")
        )

        # Build audit trail in the format required by the API contract
        audit_trail_data = audit.get_audit_trail(query_id)

        models_used = []
        preprocessing_steps = []
        parameters = {}

        for entry in audit_trail_data:
            if entry["event_type"] == "model_call":
                if entry.get("model_used"):
                    models_used.append(entry["model_used"])
                if entry.get("parameters") and isinstance(entry["parameters"], dict):
                    parameters.update(entry["parameters"])
            elif entry["event_type"] == "preprocessing":
                if entry.get("details"):
                    preprocessing_steps.append(entry["details"])

        audit_trail = AuditTrail(
            task=task_type,
            models_used=models_used if models_used else ["gemini"],
            parameters=parameters if parameters else {"query": request.query_text},
            routing_decision=routing_result.get("suggested_action"),
            preprocessing_steps=preprocessing_steps if preprocessing_steps else None
        )

        # Format visual evidence if present
        visual_evidence = None
        if result.get("visual_evidence"):
            ve = result["visual_evidence"]
            # Ensure ve is a dict
            if isinstance(ve, dict):
                visual_evidence = VisualEvidence(
                    type=ve.get("type", "unknown"),
                    data=ve.get("data"),
                    url=ve.get("url"),
                    count=ve.get("count"),
                    coverage_pct=ve.get("coverage_pct")
                )
            else:
                print(f"WARNING: visual_evidence is not a dict, it's: {type(ve)} = {ve}")
                visual_evidence = VisualEvidence(type="unknown")

        return QueryResponse(
            task=task_type,
            answer=result["answer"],
            confidence=result.get("confidence"),
            visual_evidence=visual_evidence,
            audit_trail=audit_trail
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in /query: {error_trace}")
        audit.log_event(query_id, "error", details=str(e))
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/result/{query_id}")
async def get_result(query_id: str):
    """Retrieve cached result by query ID"""
    result = db.get_query_result(query_id)
    if not result:
        raise HTTPException(status_code=404, detail="Query not found")

    # Add audit trail
    result["audit_trail"] = audit.format_audit_trail_for_ui(query_id)
    return result


@app.get("/report/{query_id}")
async def generate_report(query_id: str):
    """Generate PDF report with answer + evidence + audit trail"""
    result = db.get_query_result(query_id)
    if not result:
        raise HTTPException(status_code=404, detail="Query not found")

    # TODO: Yatharth will implement PDF generation with ReportLab
    # For now, return JSON
    audit_trail = audit.get_audit_trail(query_id)

    return JSONResponse({
        "query_id": query_id,
        "query": result["query_text"],
        "task": result["task_type"],
        "answer": result["answer"],
        "confidence": result["confidence"],
        "audit_trail": audit_trail,
        "note": "PDF generation pending - Yatharth's task"
    })


@app.get("/uploads/{session_id}/{filename}")
async def serve_uploaded_image(session_id: str, filename: str):
    """Serve uploaded images for display in browser"""
    filepath = UPLOAD_DIR / session_id / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(filepath)


# Helper functions for different task types

async def handle_vqa(query_id: str, image_info: dict, question: str) -> dict:
    """Handle single-image VQA"""
    filepath = image_info["filepath"]
    modality = image_info["modality"]

    # Load image
    audit.log_preprocessing(query_id, "image_load", f"Loading {modality} image")

    if filepath.endswith((".tif", ".tiff")):
        geo_data = load_geotiff(filepath)
        img = geo_data["image"]
        audit.log_preprocessing(query_id, "geotiff_convert", "Converted GeoTIFF to RGB")
    else:
        img = Image.open(filepath)

    # Check if SAR - in-house model required (Nisha's task)
    if modality == "sar":
        audit.log_model_call(query_id, "in-house-vqa-lora", "vqa",
                            {"image": filepath, "question": question}, success=False,
                            error="In-house SAR model not integrated yet - Nisha's task")
        # Fallback
        answer = "⚠️ SAR image detected - in-house LoRA model pending integration"
        confidence = None
    else:
        # Use Gemini for optical
        audit.log_model_call(query_id, "gemini", "vqa",
                            {"image": filepath, "question": question}, success=True)
        response = ask_vision_model(img, question, model_type="gemini")
        answer = response["answer"]
        confidence = None  # Gemini has no native confidence

        # Log confidence estimation (heuristic)
        if len(answer) > 50:  # Simple heuristic
            confidence = 0.7
            audit.log_confidence_estimation(query_id, "gemini", "heuristic:length", confidence)

    return {"answer": answer, "confidence": confidence}


async def handle_feature_mapping(query_id: str, image_info: dict, question: str) -> dict:
    """Handle feature detection/mapping"""
    filepath = image_info["filepath"]

    audit.log_preprocessing(query_id, "feature_detection", f"Detecting features: {question}")

    # Load image
    if filepath.endswith((".tif", ".tiff")):
        geo_data = load_geotiff(filepath)
        img = geo_data["image"]
    else:
        img = Image.open(filepath)

    # Use feature mapper to detect and highlight
    audit.log_model_call(query_id, "feature-mapper", "feature_detection",
                        {"image": filepath, "query": question}, success=True)

    result = detect_and_highlight(img, question)

    # Save the highlighted image
    output_filename = f"highlighted_{Path(filepath).name}"
    output_path = Path(filepath).parent / output_filename
    result['highlighted'].save(output_path)

    # Get session_id from filepath to build URL
    session_id = Path(filepath).parent.name

    return {
        "answer": result['answer'],
        "confidence": 0.85,
        "visual_evidence": {
            "type": "feature_mask",
            "path": str(output_path),
            "url": f"/uploads/{session_id}/{output_filename}",
            "count": result['count'],
            "coverage_pct": result['coverage_pct']
        }
    }


async def handle_change_detection(query_id: str, images: List[dict], question: str) -> dict:
    """Handle bi-temporal change detection"""
    img1_path = images[0]["filepath"]
    img2_path = images[1]["filepath"]

    audit.log_preprocessing(query_id, "bi_temporal_load", "Loading before/after pair")

    # Load images
    img1 = Image.open(img1_path) if not img1_path.endswith(".tif") else load_geotiff(img1_path)["image"]
    img2 = Image.open(img2_path) if not img2_path.endswith(".tif") else load_geotiff(img2_path)["image"]

    # Use existing change detection
    audit.log_model_call(query_id, "change-detector", "change_vqa",
                        {"img1": img1_path, "img2": img2_path}, success=True)

    changes = detect_changes(img1, img2)
    answer = changes["summary"]

    return {
        "answer": answer,
        "confidence": 0.8,
        "visual_evidence": {
            "type": "change_mask",
            "data": "base64_encoded_mask_placeholder"  # TODO: encode actual mask
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
