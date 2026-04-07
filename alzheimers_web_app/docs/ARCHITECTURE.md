# Architecture — Alzheimer MRI demo system

## Overview

| Layer | Stack | Role |
|-------|--------|------|
| **Frontend** | React 18, Vite, Tailwind, shadcn/ui | Single-page app; `src/lib/api.ts` talks to the backend. |
| **Backend** | FastAPI, PyTorch, torchvision | REST API: image in → JSON + optional Grad-CAM base64. |
| **Training** | PyTorch, sklearn | Stratified **train / validation / test**, checkpoint on **val macro-F1**, early stopping, exports `weights.pt`. |

## Data flow

1. User uploads an image in the browser.
2. Vite dev server proxies `/api/*` → `http://127.0.0.1:8000` (see `frontend/vite.config.ts`).
3. `POST /api/predict` reads bytes, optionally saves under `backend/uploads/`, runs `inference.predict_from_bytes`.
4. Inference loads `backend/model/weights.pt` into `build_resnet50_classifier` (same architecture as training) or falls back to legacy `alzheimer_cnn.pt`.

## Model

- **Backbone:** ResNet50 pretrained on ImageNet.
- **Head:** `Dropout` + `Linear(num_classes)`.
- **Transfer learning:** a few epochs train **head only** (backbone frozen), then **full fine-tune** with lower LR on backbone parameters.
- **Regularization:** augmentation (crop, flip, rotation, jitter, erasing), weight decay, dropout, early stopping on validation F1.

## Splits

- **Test** set is held out for the **final** metrics only (no checkpoint selection on test).
- **Validation** is used for learning-rate scheduling, best checkpoint, and early stopping.

## Configuration

- **Backend:** `backend/config.py` — paths, `MAX_UPLOAD_MB`, `CORS_ORIGINS` (env `CORS_ORIGINS=comma,separated`).
- **Production:** set `VITE_API_URL` on the frontend build to the API origin.

## Disclaimer

Research / demonstration only — not a medical device.
