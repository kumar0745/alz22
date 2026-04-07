"""Runtime configuration (paths, limits, CORS). Override via environment in deployment."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
MODEL_DIR = BACKEND_DIR / "model"
UPLOADS_DIR = BACKEND_DIR / "uploads"

# Primary artifact: state dict (portable, smaller than full pickle)
WEIGHTS_STATE_PATH = MODEL_DIR / "weights.pt"
# Legacy full-module checkpoint (older training runs)
LEGACY_FULL_MODEL_PATH = MODEL_DIR / "alzheimer_cnn.pt"

METADATA_PATH = MODEL_DIR / "model_metadata.json"
METRICS_PATH = MODEL_DIR / "training_metrics.json"

IMG_SIZE = 224

# Max upload ~15 MB (adjust for clinical DICOM pipelines if needed)
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "15")) * 1024 * 1024

# Comma-separated origins, or default dev list
_raw_cors = os.environ.get("CORS_ORIGINS", "").strip()
CORS_ORIGINS = (
    [o.strip() for o in _raw_cors.split(",") if o.strip()]
    if _raw_cors
    else [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
)
