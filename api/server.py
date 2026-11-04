"""Local FastAPI backend for InscripLens Epigraphy Studio.
Exposes existing unmodified analysis and recognition modules over local REST.
All responses are serialized to prevent internal paths, model filenames,
or stack traces from reaching the browser.
"""

from pathlib import Path
import os
import sys
import io
import json
import hashlib
from typing import List, Optional
from pydantic import BaseModel
from PIL import Image, ImageOps

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import joblib

# Ensure outputs directory is on python path for importing existing logic modules
ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = ROOT / "outputs"
if str(OUTPUTS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTPUTS_DIR))

# Import UNMODIFIED backend functions
from app_backend import ROOT as BACKEND_ROOT, analyse, history, save_review, reviews, review_export
from segment_candidates import candidates, overlay
from recognize_regions import recognize
from recognition_alternatives import rank_labels, source_examples
from run_character_benchmark import features

DATA_DIR = ROOT / "work/app_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MASK_MODELS = [
    ROOT / "outputs/broad_clean_study/mask_svm_bundle.joblib",
    ROOT / "outputs/matched_mask_study/mask_svm_bundle.joblib"
]
CLEAN_MODEL = next((p for p in MASK_MODELS if p.is_file()), MASK_MODELS[-1])

ADVANCED_MODE = os.environ.get("INSCRIPLENS_ADVANCED", "").strip().lower() in ("1", "true", "yes", "on")

app = FastAPI(title="InscripLens Studio API", version="1.0.0")

# Global exception handler to prevent any stack trace or path from leaking
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred while processing the request."}
    )

# Enable CORS for local frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local data directory for image serving
app.mount("/app_data", StaticFiles(directory=str(DATA_DIR)), name="app_data")

# Request models
class PredictCropRequest(BaseModel):
    run_id: str
    bbox: List[int]  # [x1, y1, x2, y2]

class SaveReviewRequest(BaseModel):
    run_id: str
    bbox: List[int]
    prediction: str
    model: Optional[str] = "Experimental recognizer"
    model_sha256: Optional[str] = ""
    suggestion: Optional[str] = ""
    reviewer: Optional[str] = ""
    note: Optional[str] = ""

@app.get("/api/status")
def get_status():
    """Return local asset presence and setup status without internal paths."""
    enhancement_files = [
        "work/binarizer_env/Scripts/python.exe",
        "work/shilalekhya/Unet/model.py",
        "work/shilalekhya/binarizer.pth"
    ]
    missing_enhancement = [p for p in enhancement_files if not (ROOT / p).is_file()]
    demo_path = ROOT / "outputs/full_binarizer/HS027_original.png"
    return {
        "ready": len(missing_enhancement) == 0,
        "demo_available": demo_path.is_file(),
        "recognizer_available": CLEAN_MODEL.is_file(),
        "advanced_mode": ADVANCED_MODE
    }

@app.get("/api/demo")
def get_demo_info():
    """Return demonstration stone metadata without internal paths or file names."""
    demo_path = ROOT / "outputs/full_binarizer/HS027_original.png"
    if not demo_path.is_file():
        raise HTTPException(status_code=404, detail="Demonstration stone is not available.")
    with Image.open(demo_path) as img:
        w, h = img.size
    return {
        "id": "demo_stone",
        "name": "Nagavara demonstration stone",
        "image_url": "/api/demo/image",
        "width": w,
        "height": h,
        "description": "Historical 8th-century Ganga-period inscription stone from Nagavara, Bengaluru."
    }

@app.get("/api/demo/image")
def get_demo_image():
    """Serve demo stone image without exposing internal filenames in URL."""
    demo_path = ROOT / "outputs/full_binarizer/HS027_original.png"
    if not demo_path.is_file():
        raise HTTPException(status_code=404, detail="Demonstration stone is not available.")
    return FileResponse(demo_path, media_type="image/png")

@app.post("/api/analyse")
async def run_analyse(request: Request):
    """Run Shilalekhya U-Net binarizer and candidate segmentation on stone image."""
    content_type = request.headers.get("content-type", "")
    is_demo = False
    raw = None
    filename = "stone.png"

    if "multipart/form-data" in content_type:
        form = await request.form()
        if "use_demo" in form and str(form["use_demo"]).lower() in ("true", "1"):
            is_demo = True
        elif "file" in form:
            uploaded_file = form["file"]
            if hasattr(uploaded_file, "read"):
                raw = await uploaded_file.read()
                filename = "stone.png"
    else:
        query_demo = request.query_params.get("use_demo")
        if query_demo and query_demo.lower() in ("true", "1"):
            is_demo = True

    demo_path = ROOT / "outputs/full_binarizer/HS027_original.png"
    if is_demo:
        if not demo_path.is_file():
            raise HTTPException(status_code=404, detail="Demonstration stone is not available.")
        raw = demo_path.read_bytes()
        filename = "demo.png"
    elif not raw:
        raise HTTPException(status_code=400, detail="Please select an image or the demonstration stone.")

    try:
        # Validate image and dimensions
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
        if image.width * image.height > 20_000_000:
            raise ValueError("Image exceeds 20 megapixels limit.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file. Please provide a standard image below 20 megapixels.")

    # Call existing analyse function
    try:
        record = analyse(raw, filename, DATA_DIR)
    except Exception:
        raise HTTPException(status_code=500, detail="Enhancement analysis could not be completed.")

    # Compute candidate boxes from generated mask
    mask_path = Path(record["mask_path"])
    with Image.open(mask_path) as mask:
        boxes = candidates(mask)

    # Clean display name: never expose file names
    display_name = "Nagavara demonstration stone" if is_demo else "Uploaded photograph"
    run_id = record["id"]

    return {
        "id": run_id,
        "display_name": display_name,
        "is_demo": is_demo,
        "sha256": record["sha256"],
        "image_url": f"/app_data/{run_id}/input.png",
        "mask_url": f"/app_data/{run_id}/mask.png",
        "width": image.width,
        "height": image.height,
        "boxes": boxes,
        "candidate_count": len(boxes),
        "created": record["created"]
    }

@app.post("/api/recognize-all")
def run_recognize_all(payload: dict):
    """Run batch recognition on all detected candidate regions."""
    run_id = payload.get("run_id")
    if not run_id:
        raise HTTPException(status_code=400, detail="Analysis record identifier is required.")

    mask_path = DATA_DIR / run_id / "mask.png"
    if not mask_path.is_file():
        raise HTTPException(status_code=404, detail="Selected analysis record is unavailable.")

    if not CLEAN_MODEL.is_file():
        raise HTTPException(status_code=503, detail="Character recognition is temporarily unavailable.")

    try:
        with Image.open(mask_path) as mask:
            bundle = joblib.load(CLEAN_MODEL)
            batch = recognize(mask, bundle)
    except Exception:
        raise HTTPException(status_code=500, detail="Batch character recognition could not be completed.")

    save_payload = {
        "run_id": run_id,
        "method": "predicted_mask_components_mask_svm",
        "model_sha256": hashlib.sha256(CLEAN_MODEL.read_bytes()).hexdigest(),
        "verified_transcription": False,
        "reading_order_verified": False,
        "regions": batch
    }
    json_path = DATA_DIR / run_id / "automatic_regions.json"
    json_path.write_text(json.dumps(save_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "run_id": run_id,
        "model": "Experimental recognizer",
        "candidate_count": len(batch),
        "regions": batch
    }

@app.post("/api/predict-crop")
def run_predict_crop(req: PredictCropRequest):
    """Predict character label for a specific bounding box."""
    run_id = req.run_id
    bbox = req.bbox
    if len(bbox) != 4 or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        raise HTTPException(status_code=400, detail="Invalid region coordinates selected.")

    mask_path = DATA_DIR / run_id / "mask.png"
    orig_path = DATA_DIR / run_id / "input.png"
    if not mask_path.is_file() or not orig_path.is_file():
        raise HTTPException(status_code=404, detail="Analysis image record is unavailable.")

    model_path = CLEAN_MODEL
    clean = model_path.exists()
    if not clean:
        model_path = ROOT / "outputs/training_scope_study/broader_inscriptions_svm_bundle.joblib"
    if not model_path.exists():
        raise HTTPException(status_code=503, detail="Character recognition is temporarily unavailable.")

    try:
        x1, y1, x2, y2 = bbox
        with Image.open(mask_path if clean else orig_path) as base_img:
            crop = base_img.crop((x1, y1, x2, y2))
            crop_path = DATA_DIR / run_id / f"crop_{x1}_{y1}_{x2}_{y2}.png"
            crop.save(crop_path)

        bundle = joblib.load(model_path)
        feat = features(crop_path, bundle["preprocessing"])
        alts = rank_labels(bundle["model"], feat, 3)[0]
        pred = alts[0]

        # Source examples without file paths
        ref_zip = ROOT / "outputs/recognition_references.zip"
        examples = source_examples(bundle["model"], feat, alts, model_path, ref_zip) if ref_zip.is_file() else []
        clean_examples = []
        for ex in examples:
            clean_examples.append({
                "label": ex.get("label"),
                "source_name": "Reference inscription example"
            })
    except Exception:
        raise HTTPException(status_code=500, detail="Character prediction could not be completed.")

    return {
        "run_id": run_id,
        "bbox": bbox,
        "prediction": pred,
        "alternatives": alts,
        "crop_url": f"/app_data/{run_id}/crop_{x1}_{y1}_{x2}_{y2}.png",
        "model": "Experimental recognizer",
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "reference_examples": clean_examples
    }

@app.post("/api/review")
def run_save_review(req: SaveReviewRequest):
    """Save an unverified character review record to SQLite without absolute paths."""
    model_name = "Experimental recognizer"
    reviewer_clean = (req.reviewer or "").strip()
    note_clean = (req.note or "").strip()

    try:
        save_review(
            req.run_id,
            req.bbox,
            req.prediction,
            model_name,
            req.model_sha256 or "",
            req.suggestion or "",
            reviewer_clean,
            note_clean,
            DATA_DIR
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Review record could not be saved.")

    return {"status": "saved", "run_id": req.run_id}

@app.get("/api/reviews/{run_id}")
def get_reviews_for_run(run_id: str):
    """Retrieve saved character reviews for a run, stripping any paths or internal names."""
    try:
        raw_reviews = reviews(run_id, DATA_DIR)
        sanitized = []
        for r in raw_reviews:
            item = dict(r)
            item["model"] = "Experimental recognizer"
            sanitized.append(item)
        return sanitized
    except Exception:
        raise HTTPException(status_code=500, detail="Review records could not be retrieved.")

@app.get("/api/history")
def get_analysis_history():
    """Retrieve local analysis run history stripped of absolute paths and internal filenames."""
    try:
        raw_history = history(DATA_DIR)
        sanitized = []
        for r in raw_history:
            fname = (r.get("filename") or "").lower()
            if "hs027" in fname or "demo" in fname:
                display_name = "Nagavara demonstration stone"
            else:
                display_name = "Uploaded photograph"

            sanitized.append({
                "id": r["id"],
                "created": r["created"],
                "display_name": display_name,
                "image_url": f"/app_data/{r['id']}/input.png",
                "mask_url": f"/app_data/{r['id']}/mask.png",
                "sha256": r.get("sha256", "")
            })
        return sanitized
    except Exception:
        raise HTTPException(status_code=500, detail="Analysis history could not be retrieved.")

@app.get("/api/credits")
def get_credits():
    """Return license, provenance, and attribution details."""
    return {
        "title": "InscripLens Credits & Attribution",
        "project": "Historical Kannada Inscription Image Analysis and Epigraphic Studio.",
        "components": [
            {
                "name": "Shilalekhya Pretrained U-Net Binarizer",
                "author": "IIIT Hyderabad",
                "license": "MIT Code",
                "url": "https://github.com/ihdia/shilalekhya-binarization"
            },
            {
                "name": "EpiSAM Inscriptions Dataset & Checkpoints",
                "license": "CC BY-SA 4.0",
                "acknowledgement": "Imagery acknowledged to The Mythic Society Bengaluru. Dataset previews are derived works.",
                "url": "https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset"
            }
        ]
    }

# Mount production frontend build and SPA routes if present
dist_dir = ROOT / "frontend/dist"
if dist_dir.is_dir():
    @app.get("/studio")
    def serve_studio_page():
        index_html = dist_dir / "index.html"
        if index_html.is_file():
            return FileResponse(str(index_html))
        raise HTTPException(status_code=404, detail="Studio interface not found.")

    @app.get("/about")
    @app.get("/workflow")
    @app.get("/limitations")
    @app.get("/overview")
    def serve_landing_sections():
        index_html = dist_dir / "index.html"
        if index_html.is_file():
            return FileResponse(str(index_html))
        raise HTTPException(status_code=404, detail="Page not found.")

    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")
