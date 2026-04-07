"""
FastAPI application: MRI upload → Alzheimer-stage prediction.

Routes are thin; logic lives in `inference.py`. Uploads are validated and stored under `uploads/`.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, MAX_UPLOAD_BYTES, UPLOADS_DIR
from inference import demo_full_response, minimal_json, predict_from_bytes

ALLOWED_CT = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/x-ms-bmp",
        "application/octet-stream",
    }
)

app = FastAPI(
    title="Alzheimer MRI API",
    version="3.0.0",
    description="ResNet50 MRI classification with optional Grad-CAM. See docs/ARCHITECTURE.md.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_explain(explain: str) -> bool:
    return explain.lower() in ("true", "1", "yes", "on")


async def _read_and_store_upload(image: UploadFile) -> bytes:
    if image.content_type and image.content_type not in ALLOWED_CT:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {image.content_type}. Use JPEG or PNG.",
        )
    data = await image.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(image.filename or "image.png").suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        ext = ".png"
    (UPLOADS_DIR / f"{uuid4().hex}{ext}").write_bytes(data)
    return data


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "alzheimer-mri-api"}


@app.post("/predict")
async def predict_minimal(image: UploadFile = File(...)):
    """Minimal JSON: `{ "prediction": "MCI", "confidence": 92.5 }`."""
    data = await _read_and_store_upload(image)
    return minimal_json(data)


@app.post("/predict/full")
async def predict_full(
    image: UploadFile = File(...),
    explain: str = Form("false"),
):
    """Full response + optional Grad-CAM (`explain=true`)."""
    data = await _read_and_store_upload(image)
    return predict_from_bytes(data, include_gradcam=_parse_explain(explain))


@app.post("/api/predict")
async def predict_api(
    image: UploadFile = File(...),
    explain: str = Form("false"),
):
    """Same as `/predict/full` — proxied by the Vite dev server."""
    data = await _read_and_store_upload(image)
    return predict_from_bytes(data, include_gradcam=_parse_explain(explain))


@app.get("/api/demo-prediction")
def demo_prediction():
    return demo_full_response()
