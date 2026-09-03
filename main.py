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
from backend.feature_mapper import detect_and_highlight
from backend.aryan_models import cdvqa, fusion, inhouse_vqa, gemini as aryan_gemini
from backend.aryan_preprocess import prepare_image_from_path

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
    type: str  # "feature_mask", "change_mask", "change_map", "bbox", "fusion", etc.
    data: Optional[str] = None  # base64 or URL
    url: Optional[str] = None  # URL to highlighted image
    count: Optional[int] = None
    coverage_pct: Optional[float] = None
    boxes: Optional[List[dict]] = None
    change_percentage: Optional[float] = None

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

    # Debug logging
    print(f"DEBUG: Query='{request.query_text}' -> task_type='{task_type}'")

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
        if task_type == "optical_sar_fusion" and len(images) == 2:
            result = await handle_fusion(query_id, images, request.query_text)

        elif task_type == "change_detection" and len(images) == 2:
            result = await handle_change_detection(query_id, images, request.query_text)

        elif task_type == "feature_mapping":
            result = await handle_feature_mapping(query_id, images[0], request.query_text)

        elif task_type in ["single_image", "ndvi_analysis"]:
            result = await handle_vqa(query_id, images[0], request.query_text)

        elif len(images) == 2:
            # Fallback for 2 images: if change or optical-optical -> change detection; if optical+sar -> fusion
            has_sar = any(img.get("modality") == "sar" for img in images)
            has_opt = any(img.get("modality") == "optical" for img in images)
            if has_sar and has_opt:
                result = await handle_fusion(query_id, images, request.query_text)
            else:
                result = await handle_change_detection(query_id, images, request.query_text)

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
    """Handle single-image VQA with in-house LoRA (BigEarthNet) + Gemini"""
    filepath = image_info["filepath"]
    modality = image_info.get("modality", "optical")

    audit.log_preprocessing(query_id, "image_load", f"Loading {modality} image from {Path(filepath).name}")
    prep_img = prepare_image_from_path(filepath, modality)

    for note in prep_img.notes:
        audit.log_preprocessing(query_id, "image_composite", note)

    session_id = Path(filepath).parent.name

    if prep_img.modality == "sar":
        # SAR stays strictly on in-house model (Challenge 01 & 08)
        audit.log_model_call(query_id, "in-house-lora-rsai04", "vqa",
                            {"image": filepath, "question": question, "vocabulary": "BigEarthNet-14"}, success=True)
        answer, conf, extras = inhouse_vqa.answer_vqa(prep_img, question)

        # Generate SAR visualization evidence
        evidence_filename = f"sar_evidence_{Path(filepath).stem}.png"
        evidence_path = Path(filepath).parent / evidence_filename
        prep_img.rgb.save(evidence_path)

        return {
            "answer": answer,
            "confidence": conf,
            "visual_evidence": {
                "type": "sar_backscatter_map",
                "url": f"/uploads/{session_id}/{evidence_filename}",
            }
        }
    else:
        # Optical: Gemini + in-house LoRA cross-check
        audit.log_model_call(query_id, "in-house-lora-rsai04", "vqa_class_head",
                            {"image": filepath, "question": question}, success=True)
        lora_answer, lora_conf, extras = inhouse_vqa.answer_vqa(prep_img, question)

        # Generate false-color land cover evidence overlay
        evidence_img = inhouse_vqa.overlay_class_map(prep_img)
        evidence_filename = f"landcover_evidence_{Path(filepath).stem}.png"
        evidence_path = Path(filepath).parent / evidence_filename
        evidence_img.save(evidence_path)

        # Try Groq Vision API (Llama 3.2 Vision 90B)
        audit.log_model_call(query_id, "groq-llama-3.2-vision-90b", "vqa",
                            {"image": filepath, "question": question}, success=True)

        try:
            from backend.vlm_engine import process_query
            vlm_result = process_query(prep_img.rgb, question, model_type="auto")

            if vlm_result and vlm_result.get('model_used') != 'placeholder':
                answer = f"{vlm_result['answer']}\n\n🔍 In-House LoRA Land-Cover Head: {lora_answer}"
                confidence = min(0.94, lora_conf + 0.10)
            else:
                raise Exception("VLM returned placeholder response")
        except Exception as e:
            print(f"Vision API failed for VQA: {e}")
            # Enhanced fallback answer
            answer = f"**Land Cover Analysis:** {lora_answer}\n\n**Note:** This analysis is based on our in-house remote sensing model trained on BigEarthNet. For detailed scene interpretation with AI vision models, please ensure GROQ_API_KEY is set in your .env file."
            confidence = lora_conf

        return {
            "answer": answer,
            "confidence": confidence,
            "visual_evidence": {
                "type": "spectral_class_map",
                "url": f"/uploads/{session_id}/{evidence_filename}",
            }
        }


async def handle_change_detection(query_id: str, images: List[dict], question: str) -> dict:
    """Handle bi-temporal Change VQA with CDVQA + Siamese patch head + Gemini"""
    img1_path = images[0]["filepath"]
    img2_path = images[1]["filepath"]

    audit.log_preprocessing(query_id, "bi_temporal_load", "Loading before/after pair for co-registration")

    p1 = prepare_image_from_path(img1_path, images[0].get("modality", "optical"))
    p2 = prepare_image_from_path(img2_path, images[1].get("modality", "optical"))

    for note in p1.notes + p2.notes:
        audit.log_preprocessing(query_id, "image_prep", note)

    # Run Aryan's CDVQA
    audit.log_model_call(query_id, "cdvqa-siamese-head", "change_vqa",
                        {"before": img1_path, "after": img2_path, "question": question}, success=True)

    local_cdvqa = cdvqa.run_cdvqa(p1, p2, question)

    # Save visual overlay
    session_id = Path(img1_path).parent.name
    output_filename = f"change_overlay_{Path(img1_path).stem}_{Path(img2_path).stem}.png"
    output_path = Path(img1_path).parent / output_filename
    local_cdvqa["overlay"].save(output_path)

    # Convert bounding boxes to frontend percentage format
    w, h = local_cdvqa["after_aligned"].size
    frontend_boxes = []
    for idx, (x0, y0, x1, y1) in enumerate(local_cdvqa.get("boxes", [])[:4]):
        frontend_boxes.append({
            "id": f"CHG_{idx+1:02d}",
            "x": round((x0 / w) * 100, 1),
            "y": round((y0 / h) * 100, 1),
            "width": round(((x1 - x0) / w) * 100, 1),
            "height": round(((y1 - y0) / h) * 100, 1)
        })

    # Try Gemini on optical pairs
    gemini_text = ""
    if p1.modality == "optical" and p2.modality == "optical":
        audit.log_model_call(query_id, "gemini-change-vqa", "change_vqa",
                            {"prompt": question}, success=True)
        prompt = (
            "You are a remote-sensing change-detection analyst for satellite imagery. "
            "Image 1 is BEFORE, Image 2 is AFTER. Answer the question directly and concisely. "
            "Cite visible changes like flooding, new construction, damage, or vegetation shifts.\n\n"
            f"Question: {question}"
        )
        g = aryan_gemini.generate(prompt, [p1.rgb, p2.rgb])
        if g.ok:
            gemini_text = g.text

    if gemini_text:
        answer = f"{gemini_text}\n\n🛰️ CDVQA Spectral & Spatial Analysis:\n{local_cdvqa['answer']}"
        confidence = min(0.95, local_cdvqa["confidence"] + 0.08)
    else:
        answer = local_cdvqa["answer"]
        confidence = local_cdvqa["confidence"]

    audit.log_preprocessing(query_id, "visual_evidence", f"Generated change map with {len(frontend_boxes)} hotspot boxes")

    return {
        "answer": answer,
        "confidence": confidence,
        "visual_evidence": {
            "type": "change_map",
            "url": f"/uploads/{session_id}/{output_filename}",
            "change_percentage": round(local_cdvqa["change_ratio"] * 100, 2),
            "boxes": frontend_boxes,
            "siamese_peak": round(local_cdvqa.get("siamese_peak", 0.0), 3)
        }
    }


async def handle_fusion(query_id: str, images: List[dict], question: str) -> dict:
    """Handle Optical + SAR Dual-Encoder Fusion"""
    img1_info = images[0]
    img2_info = images[1]

    # Find optical and sar
    if img1_info.get("modality") == "sar":
        sar_info, opt_info = img1_info, img2_info
    else:
        opt_info, sar_info = img1_info, img2_info

    audit.log_preprocessing(query_id, "fusion_load", "Loading optical RGB + Sentinel-1 SAR pair")

    optical_p = prepare_image_from_path(opt_info["filepath"], "optical")
    sar_p = prepare_image_from_path(sar_info["filepath"], "sar")

    audit.log_model_call(query_id, "dual-encoder-fusion", "optical_sar_fusion",
                        {"optical": opt_info["filepath"], "sar": sar_info["filepath"]}, success=True)

    fused = fusion.fuse(optical_p, sar_p)

    session_id = Path(opt_info["filepath"]).parent.name
    output_filename = f"fusion_overlay_{Path(opt_info['filepath']).stem}_{Path(sar_info['filepath']).stem}.png"
    output_path = Path(opt_info["filepath"]).parent / output_filename
    fused["overlay"].save(output_path)

    return {
        "answer": fused["answer"],
        "confidence": fused["confidence"],
        "visual_evidence": {
            "type": "optical_sar_fusion",
            "url": f"/uploads/{session_id}/{output_filename}"
        }
    }


async def handle_feature_mapping(query_id: str, image_info: dict, question: str) -> dict:
    """Handle feature detection/mapping with AI contextual analysis"""
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

    # Add AI contextual analysis
    prep_img = prepare_image_from_path(filepath, image_info.get("modality", "optical"))

    # Get land-cover classification from in-house VQA
    audit.log_model_call(query_id, "in-house-lora-context", "land_cover",
                        {"image": filepath}, success=True)
    lora_answer, lora_conf, extras = inhouse_vqa.answer_vqa(prep_img, "Describe the land cover and urban features")

    # Get Groq's interpretation if available
    audit.log_model_call(query_id, "groq-llama-3.2-vision-90b", "contextual_analysis",
                        {"image": filepath, "question": question}, success=True)

    groq_prompt = (
        f"You are analyzing a satellite image where {result['count']} features were detected "
        f"covering {result['coverage_pct']:.1f}% of the area. "
        f"Answer this question about the image: {question}\n\n"
        "Provide insights about urban planning, infrastructure patterns, and spatial organization."
    )

    try:
        from backend.vlm_engine import process_query
        vlm_result = process_query(prep_img.rgb, groq_prompt, model_type="auto")

        if vlm_result and vlm_result.get('model_used') != 'placeholder':
            answer = (
                f"{vlm_result['answer']}\n\n"
                f"📊 Detection Results: {result['count']} features detected, "
                f"covering {result['coverage_pct']:.1f}% of the image area.\n\n"
                f"🗺️ Land Cover Analysis: {lora_answer}"
            )
            confidence = min(0.92, lora_conf + 0.10)
        else:
            raise Exception("VLM returned placeholder response")
    except Exception as e:
        # Log why vision API failed
        print(f"Vision API failed for feature mapping: {e}")
        answer = (
            f"{result['answer']}\n\n"
            f"🗺️ Land Cover Context: {lora_answer}"
        )
        confidence = 0.85

    return {
        "answer": answer,
        "confidence": confidence,
        "visual_evidence": {
            "type": "feature_mask",
            "path": str(output_path),
            "url": f"/uploads/{session_id}/{output_filename}",
            "count": result['count'],
            "coverage_pct": result['coverage_pct']
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
