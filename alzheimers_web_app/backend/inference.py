"""Model loading and prediction payloads (shared types for /predict and /api/predict)."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import torch

from config import LEGACY_FULL_MODEL_PATH, METADATA_PATH, WEIGHTS_STATE_PATH
from gradcam_service import compute_gradcam, overlay_cam_base64
from labels import (
    CLASS_TO_SHORT,
    CLASS_TO_UI_STAGE,
    UI_EXPLANATIONS,
    UI_STAGE_TO_SHORT,
)
from model_factory import build_resnet50_classifier
from preprocessing import image_to_tensor, load_image_from_bytes

_model: torch.nn.Module | None = None
_class_names: list[str] | None = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_metadata() -> dict[str, Any]:
    if not METADATA_PATH.is_file():
        return {
            "class_names": list(CLASS_TO_UI_STAGE.keys()),
            "num_classes": len(CLASS_TO_UI_STAGE),
            "dropout": 0.4,
        }
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def load_model() -> tuple[torch.nn.Module | None, list[str]]:
    """Load once; prefer state_dict + metadata over legacy full-model pickle."""
    global _model, _class_names
    if _model is not None and _class_names is not None:
        return _model, _class_names

    meta = _load_metadata()
    class_names = list(meta.get("class_names") or CLASS_TO_UI_STAGE.keys())
    num_classes = int(meta.get("num_classes", len(class_names)))
    dropout = float(meta.get("dropout", 0.4))

    if WEIGHTS_STATE_PATH.is_file():
        m = build_resnet50_classifier(num_classes, dropout_p=dropout).to(_device)
        try:
            state = torch.load(WEIGHTS_STATE_PATH, map_location=_device, weights_only=True)
        except TypeError:
            state = torch.load(WEIGHTS_STATE_PATH, map_location=_device)
        m.load_state_dict(state)
        m.eval()
        _model, _class_names = m, class_names
        return _model, _class_names

    if LEGACY_FULL_MODEL_PATH.is_file():
        try:
            mapped = torch.load(LEGACY_FULL_MODEL_PATH, map_location=_device, weights_only=False)
        except TypeError:
            mapped = torch.load(LEGACY_FULL_MODEL_PATH, map_location=_device)
        if hasattr(mapped, "eval"):
            mapped.eval()
            _model, _class_names = mapped, class_names
            return _model, _class_names

    _model, _class_names = None, class_names
    return _model, _class_names


def clear_model_cache() -> None:
    """For tests or hot-reload (optional)."""
    global _model, _class_names
    _model, _class_names = None, None


def demo_full_response() -> dict[str, Any]:
    stages = [
        {"stage": "Normal", "probability": 4.2},
        {"stage": "Very Mild Impairment", "probability": 12.8},
        {"stage": "Mild Cognitive Impairment", "probability": 72.5},
        {"stage": "Alzheimer's Disease", "probability": 10.5},
    ]
    top = max(stages, key=lambda x: x["probability"])
    code = UI_STAGE_TO_SHORT.get(top["stage"], "MCI")
    return {
        "prediction": code,
        "confidence": round(float(top["probability"]), 2),
        "prediction_full": top["stage"],
        "prediction_code": code,
        "details": stages,
        "explanation": UI_EXPLANATIONS.get(
            top["stage"],
            "Automated assessment complete. Consult a clinician for diagnosis.",
        ),
        "source": "demo",
        "gradcam_base64": None,
    }


def predict_from_bytes(
    data: bytes,
    *,
    include_gradcam: bool,
) -> dict[str, Any]:
    pil = load_image_from_bytes(data)
    model, class_names = load_model()

    if model is None:
        return demo_full_response()

    x = image_to_tensor(pil).to(_device)
    with torch.inference_mode():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

    order = np.argsort(-probs)
    details = []
    for i in order:
        folder = class_names[int(i)]
        ui_stage = CLASS_TO_UI_STAGE.get(folder, folder)
        details.append({"stage": ui_stage, "probability": float(probs[i] * 100.0)})

    top_i = int(order[0])
    top_folder = class_names[top_i]
    ui_top = CLASS_TO_UI_STAGE.get(top_folder, top_folder)
    short = CLASS_TO_SHORT.get(top_folder, ui_top)
    conf_pct = float(probs[top_i] * 100.0)

    gradcam_b64: str | None = None
    if include_gradcam:
        try:
            x_req = image_to_tensor(pil).to(_device)
            x_req.requires_grad_(True)
            with torch.set_grad_enabled(True):
                cam = compute_gradcam(model, x_req, top_i)
            gradcam_b64 = overlay_cam_base64(pil, cam)
        except Exception:
            gradcam_b64 = None

    return {
        "prediction": short,
        "confidence": round(conf_pct, 2),
        "prediction_full": ui_top,
        "prediction_code": short,
        "details": details,
        "explanation": UI_EXPLANATIONS.get(
            ui_top,
            "Automated assessment complete. Consult a clinician for diagnosis.",
        ),
        "source": "model",
        "gradcam_base64": gradcam_b64,
    }


def minimal_json(data: bytes) -> dict[str, Any]:
    full = predict_from_bytes(data, include_gradcam=False)
    return {
        "prediction": full["prediction"],
        "confidence": full["confidence"],
    }
